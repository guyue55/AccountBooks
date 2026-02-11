"""
AccountBooks 数据模型模块。

定义了系统的核心业务实体，包括：
- Account: 债务人基本分类
- AccountInfo: 债务人详细信息
- GoodsInfo: 商品及定价
- Order: 交易订单头
- OrderItem: 订单行项（商品×数量×小计）
- AccountBooks: 债务人账务汇总
"""

from decimal import Decimal

from django.db import models
from django.db.models import Sum
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone


class Account(models.Model):
    """记录债务人的基本分类信息。

    Attributes:
        name: 债务人的唯一标识名称。
    """
    name = models.CharField('债务人', max_length=50, unique=True)

    def __str__(self):
        """返回债务人名称。"""
        return self.name

    class Meta:
        verbose_name = '债务人'
        verbose_name_plural = '债务人列表'
        db_table = 'accounts'
        ordering = ['name']


class AccountInfo(models.Model):
    """记录债务人的详细个人信息及关联。

    Attributes:
        name: 债务人显示名称。
        real_name: 真实姓名。
        age: 年龄。
        location: 地址或所属地区。
        remarks: 备注信息。
        created: 创建时间。
        updated: 更新时间。
    """
    name = models.CharField(max_length=50, verbose_name='债务人', default="")
    real_name = models.CharField(max_length=50, verbose_name='真实姓名', default="")
    age = models.IntegerField(verbose_name='年龄', default=0)
    location = models.CharField(max_length=100, verbose_name='地址', default="未知地区")
    remarks = models.CharField(max_length=200, verbose_name='备注', default="")
    created = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    def __str__(self):
        """返回债务人及其地址的组合描述。"""
        return f"{self.name}: {self.location}"

    class Meta:
        verbose_name = '债务人详情'
        verbose_name_plural = '债务人详情列表'
        db_table = 'accounts_info'
        ordering = ['name']


class GoodsInfo(models.Model):
    """记录商品及其单价信息。

    Attributes:
        goods: 商品名称。
        goods_price: 商品单价（元），使用 DecimalField 确保精度。
        created: 创建时间。
        updated: 更新时间。
    """
    goods = models.CharField(max_length=50, verbose_name='商品名称', default="其它")
    goods_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, verbose_name='单价（元）'
    )
    created = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    def __str__(self):
        """返回商品名称及单价。"""
        return f"{self.goods} (¥{self.goods_price})"

    class Meta:
        verbose_name = '商品信息'
        verbose_name_plural = '商品信息列表'
        db_table = 'goods_info'
        ordering = ['goods']


class Order(models.Model):
    """记录具体的交易订单头信息。

    订单的商品明细通过 OrderItem 关联管理，每个商品可独立设置数量。
    total_price 由 calc_total() 方法根据 OrderItem 自动计算。

    Attributes:
        account: 购买人（关联 AccountInfo）。
        total_price: 应收总价（由行项合计自动生成）。
        total_price_real: 实收总价（手动输入）。
        buy_time: 购买时间。
        status: 还款状态。
    """
    STATUS_CHOICES = (
        ('wait', '待还'),
        ('ok', '已还'),
        ('default', '赖账'),
        ('unknown', '未知'),
    )

    account = models.ForeignKey(
        AccountInfo, on_delete=models.CASCADE, verbose_name='购买人'
    )
    total_price = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00, verbose_name='总价（应收）'
    )
    total_price_real = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00, verbose_name='总价（实收）'
    )
    buy_time = models.DateTimeField(default=timezone.now, verbose_name='购买时间')
    created = models.DateTimeField(auto_now_add=True, verbose_name='创建日期')
    updated = models.DateTimeField(auto_now=True, verbose_name='更新日期')
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='wait', verbose_name='还款状态'
    )

    def calc_total(self):
        """根据关联的 OrderItem 重新计算应收总价并保存。

        遍历所有行项的 subtotal 求和写入 total_price 字段。
        """
        total = self.items.aggregate(total=Sum('subtotal'))['total'] or Decimal('0.00')
        self.total_price = total
        self.save(update_fields=['total_price'])

    def __str__(self):
        """返回订单详情摘要。"""
        return (f"订单ID:{self.id} | 购买人:{self.account.name} | "
                f"应收:{self.total_price}元 | 状态:{self.get_status_display()}")

    class Meta:
        verbose_name = '交易记录'
        verbose_name_plural = '交易记录列表'
        db_table = 'accounts_orders'
        ordering = ['-buy_time']


class OrderItem(models.Model):
    """订单行项 —— 记录每个商品在订单中的独立数量和小计。

    通过 through 中间表替代之前 Order.goods 的 ManyToMany + 单一 goods_number 的设计，
    支持每个商品设置不同数量，并快照下单时的单价。

    Attributes:
        order: 关联的订单。
        goods: 关联的商品。
        quantity: 购买数量。
        unit_price: 下单时的单价快照（避免后续商品调价影响历史订单）。
        subtotal: 小计金额（quantity × unit_price）。
    """
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='items', verbose_name='订单'
    )
    goods = models.ForeignKey(
        GoodsInfo, on_delete=models.PROTECT, verbose_name='商品'
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name='数量')
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, verbose_name='单价（快照）'
    )
    subtotal = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00, verbose_name='小计'
    )

    def save(self, *args, **kwargs):
        """保存前自动计算小计金额。

        如果 unit_price 未手动设置（为 0），则从关联商品取当前单价。
        """
        if self.unit_price == Decimal('0.00') and self.goods_id:
            self.unit_price = self.goods.goods_price
        self.subtotal = self.unit_price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        """返回行项描述。"""
        return f"{self.goods.goods} ×{self.quantity} = {self.subtotal}元"

    class Meta:
        verbose_name = '订单行项'
        verbose_name_plural = '订单行项列表'
        db_table = 'order_items'


class AccountBooks(models.Model):
    """记录每个债务人的账务汇总。

    Attributes:
        account_info: 关联的债务人详情。
        money_total: 累计应收总金额。
        money_wait: 当前待还总金额。
        money_over: 已还总金额。
        money_default: 确认赖账的金额。
    """
    account_info = models.ForeignKey(
        AccountInfo, on_delete=models.CASCADE, verbose_name='债务人信息'
    )
    money_total = models.DecimalField(
        max_digits=15, decimal_places=2, default=0.00, verbose_name='总金额（应收）'
    )
    money_wait = models.DecimalField(
        max_digits=15, decimal_places=2, default=0.00, verbose_name='待还金额'
    )
    money_over = models.DecimalField(
        max_digits=15, decimal_places=2, default=0.00, verbose_name='已还金额'
    )
    money_default = models.DecimalField(
        max_digits=15, decimal_places=2, default=0.00, verbose_name='赖账金额'
    )
    created = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    def update_summary(self):
        """根据关联的所有订单重新计算账务汇总。

        该方法会遍历关联的所有订单，并根据订单状态更新汇总字段。
        """
        orders = Order.objects.filter(account=self.account_info)
        self.money_total = Decimal('0.00')
        self.money_wait = Decimal('0.00')
        self.money_over = Decimal('0.00')
        self.money_default = Decimal('0.00')

        for order in orders:
            self.money_total += order.total_price
            if order.status == 'ok':
                self.money_over += order.total_price_real
            elif order.status == 'wait':
                self.money_wait += order.total_price
            elif order.status == 'default':
                self.money_default += order.total_price

        self.save()

    def __str__(self):
        """返回账簿汇总摘要。"""
        return f"{self.account_info.name} | 待还: {self.money_wait}元 | 赖账: {self.money_default}元"

    class Meta:
        verbose_name = '账簿总览'
        verbose_name_plural = '账簿总览列表'
        db_table = 'accounts_books'
        ordering = ['-money_wait']


# ===== 信号处理 =====
# 确保在订单或订单行项保存/删除后，自动更新对应的账簿汇总和订单总价

@receiver(post_save, sender=Order)
@receiver(post_delete, sender=Order)
def update_account_books(sender, instance, **kwargs):
    """当订单发生变化时，自动刷新对应债务人的账务汇总数据。"""
    account_book, _ = AccountBooks.objects.get_or_create(
        account_info=instance.account
    )
    account_book.update_summary()


@receiver(post_save, sender=OrderItem)
@receiver(post_delete, sender=OrderItem)
def update_order_total_on_item_change(sender, instance, **kwargs):
    """当订单行项发生变化时，自动重新计算订单应收总价。"""
    try:
        instance.order.calc_total()
    except Order.DoesNotExist:
        # 订单已被删除，无需处理
        pass
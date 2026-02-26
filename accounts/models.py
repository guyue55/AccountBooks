"""
AccountBooks 数据模型模块。

定义了系统的核心业务实体，包括：
- AccountInfo: 债务人详细信息
- GoodsInfo: 商品及定价
- Order: 交易订单头
- OrderItem: 订单行项（商品×数量×小计）
- AccountBooks: 债务人账务汇总
"""

from decimal import Decimal

from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum, Case, When, Value, DecimalField
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone


class UserProfile(models.Model):
    """用户个性化设置模型。"""
    THEME_CHOICES = (
        ('dark', 'Linear Dark'),
        ('light', 'Vercel Light'),
        ('nord', 'Nordic Frost'),
        ('purple', 'Midnight Amethyst'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    theme = models.CharField(max_length=20, choices=THEME_CHOICES, default='dark', verbose_name='系统主题')

    def __str__(self):
        return f"{self.user.username} 的个人设置"

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            UserProfile.objects.create(user=instance)

    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        if not hasattr(instance, 'profile'):
            UserProfile.objects.create(user=instance)
        instance.profile.save()


class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        """批量执行逻辑删除，返回与 Django 原生 delete() 相同格式的 (count, dict) 元组。"""
        count = self.count()
        self.update(is_deleted=True, deleted_at=timezone.now())
        # 返回 (数量, {model_label: 数量}) 以兼容需要解包的调用方
        model_label = f"{self.model._meta.app_label}.{self.model.__name__}"
        return count, {model_label: count}


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        """默认只查询未删除的数据。"""
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)


class SoftDeleteModel(models.Model):
    """逻辑删除基类。"""
    is_deleted = models.BooleanField(default=False, verbose_name='已删除')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='删除时间')

    objects = SoftDeleteManager()  # 默认管理器：只返回未删除
    all_objects = models.Manager() # 包含已删除的源生管理器

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """执行逻辑删除而非物理删除。"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])


class AccountInfo(SoftDeleteModel):
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
    real_name = models.CharField(max_length=50, verbose_name='真实姓名', default="", blank=True)
    age = models.IntegerField(verbose_name='年龄', default=0, blank=True)
    phone = models.CharField(max_length=20, verbose_name='联系电话', default="", blank=True)
    location = models.CharField(max_length=100, verbose_name='地址', default="未知地区", blank=True)
    remarks = models.CharField(max_length=200, verbose_name='备注', default="", blank=True)
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


class GoodsInfo(SoftDeleteModel):
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
    purchase_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, verbose_name='进价（元）', blank=True, null=True
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
        constraints = [
            # 仅对未删除的商品施加名称唯一约束
            # 允许"重名"的已软删除商品继续留存，不阻塞重建同名商品
            models.UniqueConstraint(
                fields=['goods'],
                condition=models.Q(is_deleted=False),
                name='unique_active_goods_name'
            )
        ]


class Order(SoftDeleteModel):
    """记录具体的交易订单头信息。

    订单的商品明细通过 OrderItem 关联管理，每个商品可独立设置数量。
    total_price 由 calc_total() 方法根据 OrderItem 自动计算。

    Attributes:
        account: 顾客（关联 AccountInfo）。
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
        AccountInfo, on_delete=models.CASCADE, verbose_name='顾客'
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
        
        注意：因为 OrderItem 已启用逻辑删除，.items.all() 会自动过滤掉已删除项。
        """
        total = self.items.aggregate(total=Sum('subtotal'))['total'] or Decimal('0.00')
        self.total_price = total
        self.save(update_fields=['total_price'])

    def __str__(self):
        """返回订单详情摘要。"""
        return (f"订单ID:{self.id} | 顾客:{self.account.name} | "
                f"应收:{self.total_price}元 | 状态:{self.get_status_display()}")

    class Meta:
        verbose_name = '交易记录'
        verbose_name_plural = '交易记录列表'
        db_table = 'accounts_orders'
        ordering = ['-buy_time']


class OrderItem(SoftDeleteModel):
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
        """保存前自动计算小计金额。"""
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


class AccountBooks(SoftDeleteModel):
    """记录每个债务人的账务汇总。

    Attributes:
        account_info: 关联的债务人详情。calc_total
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
        
        注意：因为 Order 已启用逻辑删除，默认只统计未删除的订单。
        """
        orders = Order.objects.filter(account=self.account_info)
        
        aggregates = orders.aggregate(
            total=Sum('total_price'),
            wait=Sum(Case(
                When(status='wait', then='total_price'),
                default=Value(0),
                output_field=DecimalField()
            )),
            over=Sum(Case(
                When(status='ok', then='total_price_real'),
                default=Value(0),
                output_field=DecimalField()
            )),
            default=Sum(Case(
                When(status='default', then='total_price'),
                default=Value(0),
                output_field=DecimalField()
            ))
        )
        
        self.money_total = aggregates.get('total') or Decimal('0.00')
        self.money_wait = aggregates.get('wait') or Decimal('0.00')
        self.money_over = aggregates.get('over') or Decimal('0.00')
        self.money_default = aggregates.get('default') or Decimal('0.00')

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

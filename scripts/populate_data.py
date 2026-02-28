import os
import random
from datetime import timedelta
from decimal import Decimal

import django
from django.utils import timezone

# 设置 Django 环境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "AccountBooks.settings")
django.setup()


def create_sample_data():
    """清理旧数据并生成示例数据，包括商品、客户和订单.

    该函数执行以下操作：
    1. 删除现有的 OrderItem, Order, AccountBooks, GoodsInfo 和 AccountInfo 数据。
    2. 创建预定义的商品列表。
    3. 创建示例客户信息。
    4. 随机生成最近 30 天内的订单，并关联商品和计算金额。
    5. 更新客户的账本摘要。
    """
    # 在函数内部导入，以满足 PEP 8 规范并确保 django.setup() 先执行
    from accounts.models import AccountBooks, AccountInfo, GoodsInfo, Order, OrderItem

    print("🧹 Cleaning old data...")
    OrderItem.objects.all().delete()
    Order.objects.all().delete()
    AccountBooks.objects.all().delete()
    GoodsInfo.objects.all().delete()
    AccountInfo.objects.all().delete()

    print("📦 Creating goods...")
    goods_data = [
        ("华硕笔记本电脑", 5999.00, 5200.00),
        ("华为 P60 Pro", 6988.00, 6100.00),
        ("AirPods Pro 2", 1899.00, 1550.00),
        ("罗技 G502 鼠标", 399.00, 280.00),
        ("机械键盘 K70", 899.00, 650.00),
        ("27寸 4K 显示器", 2499.00, 1900.00),
        ("小米插线板", 49.00, 35.00),
        ("移动硬盘 2TB", 459.00, 320.00),
        ("三只松鼠大礼包", 128.00, 85.00),
        ("得力 A4 打印纸", 25.00, 18.00),
    ]

    goods_objs = []
    for name, price, p_price in goods_data:
        g = GoodsInfo.objects.create(
            goods=name, goods_price=price, purchase_price=p_price
        )
        goods_objs.append(g)

    print("👤 Creating customers...")
    customers_data = [
        ("张伟", "张大伟", 28, "北京市海淀区", "13800138000", "老客户"),
        ("李娜", "李丽娜", 25, "上海市浦东新区", "13912345678", "公司财务"),
        ("王强", "王小强", 32, "深圳市南山区", "13788889999", "技术支持"),
        ("刘洋", "刘大洋", 22, "杭州市西湖区", "13600001111", "学生"),
        ("陈思", "陈思思", 29, "广州市天河区", "15011112222", "设计总监"),
        ("赵雷", "赵天雷", 35, "成都市武侯区", "18877776666", "个体户"),
    ]

    customer_objs = []
    for name, real_name, age, loc, phone, rem in customers_data:
        c = AccountInfo.objects.create(
            name=name,
            real_name=real_name,
            age=age,
            location=loc,
            phone=phone,
            remarks=rem,
        )
        customer_objs.append(c)

    print("📜 Creating orders...")
    statuses = ["wait", "ok", "default"]

    for _ in range(30):
        customer = random.choice(customer_objs)
        # 随机过去 30 天的时间
        days_ago = random.randint(0, 30)
        buy_time = timezone.now() - timedelta(days=days_ago)

        status = random.choices(statuses, weights=[60, 30, 10])[0]

        order = Order.objects.create(account=customer, buy_time=buy_time, status=status)

        # 每个订单 1-3 个商品
        selected_goods = random.sample(goods_objs, random.randint(1, 3))
        for g in selected_goods:
            OrderItem.objects.create(
                order=order,
                goods=g,
                quantity=random.randint(1, 5),
                unit_price=g.goods_price,
            )

        # 计算总价
        order.calc_total()

        # 如果是已还，随机设置实收金额（通常等于应收，或者略少一点作为抹零）
        if status == "ok":
            if random.random() > 0.8:
                order.total_price_real = order.total_price - Decimal("5.00")
            else:
                order.total_price_real = order.total_price
            order.save()

    print("📊 Updating summaries...")
    for customer in customer_objs:
        book, created = AccountBooks.objects.get_or_create(account_info=customer)
        book.update_summary()

    print("✅ Data generation complete!")


if __name__ == "__main__":
    create_sample_data()

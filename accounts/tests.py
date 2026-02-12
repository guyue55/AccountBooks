from decimal import Decimal
from django.test import TestCase
from accounts.models import AccountInfo, GoodsInfo, Order, OrderItem, AccountBooks

class OrderTestCase(TestCase):
    def setUp(self):
        self.account = AccountInfo.objects.create(name="Test User")
        self.goods = GoodsInfo.objects.create(goods="Apple", goods_price=Decimal("10.00"))
    
    def test_calc_total(self):
        """测试订单总价自动计算逻辑"""
        order = Order.objects.create(account=self.account)
        # 添加商品行项，数量为 2，单价 10.00，小计应为 20.00
        OrderItem.objects.create(order=order, goods=self.goods, quantity=2)
        
        # 检查订单总价是否自动更新（通过信号触发）
        order.refresh_from_db()
        self.assertEqual(order.total_price, Decimal("20.00"))
        
        # 修改数量为 3，小计应为 30.00
        item = order.items.first()
        item.quantity = 3
        item.save()
        
        order.refresh_from_db()
        self.assertEqual(order.total_price, Decimal("30.00"))

class AccountBooksTestCase(TestCase):
    def setUp(self):
        self.account = AccountInfo.objects.create(name="Test User")
        self.goods = GoodsInfo.objects.create(goods="Apple", goods_price=Decimal("100.00"))
        
    def test_update_summary(self):
        """测试账簿汇总自动更新逻辑 (聚合计算)"""
        # 1. 创建待还订单 (Wait): 应收 100
        order1 = Order.objects.create(account=self.account, status='wait')
        OrderItem.objects.create(order=order1, goods=self.goods, quantity=1) 
        
        # 2. 创建已还订单 (OK): 应收 100，实收 50
        order2 = Order.objects.create(account=self.account, status='ok', total_price_real=Decimal("50.00"))
        OrderItem.objects.create(order=order2, goods=self.goods, quantity=1)
        
        # 3. 创建赖账订单 (Default): 应收 100
        order3 = Order.objects.create(account=self.account, status='default')
        OrderItem.objects.create(order=order3, goods=self.goods, quantity=1)
        
        # 检查汇总数据
        # 信号应该自动创建并更新 AccountBooks
        books = AccountBooks.objects.get(account_info=self.account)
        
        self.assertEqual(books.money_wait, Decimal("100.00"))     # order1
        self.assertEqual(books.money_over, Decimal("50.00"))      # order2 (实收)
        self.assertEqual(books.money_default, Decimal("100.00"))  # order3
        self.assertEqual(books.money_total, Decimal("300.00"))    # order1 + order2 + order3 (应收总和)

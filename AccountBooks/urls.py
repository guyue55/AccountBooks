"""AccountBooks URL Configuration

路由配置模块，包含以下功能组：
- 认证：登录 / 注册 / 退出
- Dashboard：首页总览
- 交易记录：CRUD 操作
- 商品管理：CRUD 操作
- 顾客管理：CRUD 操作
- API：价格计算接口
- 管理后台：Django Admin
"""

from django.conf.urls import url, include
from django.contrib import admin
from django.urls import path

from accounts import views

urlpatterns = [
    # ----- 管理后台 -----
    path('admin/', admin.site.urls),
    path('books/', include('accounts.urls', namespace='books')),

    # ----- 认证 -----
    path('login', views.LoginView.as_view(), name='login'),
    path('register', views.RegisterView.as_view(), name='register'),
    path('logout', views.LogoutView.as_view(), name='logout'),

    # ----- Dashboard -----
    path('', views.DashboardView.as_view(), name='index'),

    # ----- 交易记录 -----
    path('orders', views.OrdersView.as_view(), name='orders'),
    path('orders/add', views.OrderCreateView.as_view(), name='order_add'),
    path('orders/<int:pk>/edit', views.OrderUpdateView.as_view(), name='order_edit'),
    path('orders/<int:pk>/delete', views.OrderDeleteView.as_view(), name='order_delete'),

    # ----- 商品管理 -----
    path('goods', views.GoodsListView.as_view(), name='goods_list'),
    path('goods/add', views.GoodsCreateView.as_view(), name='goods_add'),
    path('goods/<int:pk>/edit', views.GoodsUpdateView.as_view(), name='goods_edit'),
    path('goods/<int:pk>/delete', views.GoodsDeleteView.as_view(), name='goods_delete'),

    # ----- 顾客管理 -----
    path('customers', views.CustomerListView.as_view(), name='customer_list'),
    path('customers/add', views.CustomerCreateView.as_view(), name='customer_add'),
    path('customers/<int:pk>/edit', views.CustomerUpdateView.as_view(), name='customer_edit'),
    path('customers/<int:pk>/delete', views.CustomerDeleteView.as_view(), name='customer_delete'),

    # ----- API -----
    path('api/calc-price', views.CalcPriceAPI.as_view(), name='calc_price'),

    # ----- 兼容旧路由 -----
    path('work', views.WorkView.as_view(), name='work'),
    path('404', views.Page404View.as_view(), name='page404'),
    path('list', views.RedirectToLoginView.as_view(), name='show_list'),
]

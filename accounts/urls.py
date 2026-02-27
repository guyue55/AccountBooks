from django.urls import path, re_path
from . import views

urlpatterns = [
    # ----- Dashboard -----
    path('', views.DashboardView.as_view(), name='index'),
    re_path(r'^(?P<path>.*)/$', views.DashboardView.as_view(), name='index_trailing'),

    # ----- 认证 -----
    path('login', views.LoginView.as_view(), name='login'),
    re_path(r'^login/$', views.LoginView.as_view(), name='login'),
    path('register', views.RegisterView.as_view(), name='register'),
    re_path(r'^register/$', views.RegisterView.as_view(), name='register'),
    path('logout', views.LogoutView.as_view(), name='logout'),
    re_path(r'^logout/$', views.LogoutView.as_view(), name='logout'),

    # ----- 交易记录 -----
    path('orders', views.OrdersView.as_view(), name='orders'),
    re_path(r'^orders/$', views.OrdersView.as_view(), name='orders'),
    path('orders/add', views.OrderCreateView.as_view(), name='order_add'),
    re_path(r'^orders/add/$', views.OrderCreateView.as_view(), name='order_add'),
    path('orders/<int:pk>/edit', views.OrderUpdateView.as_view(), name='order_edit'),
    re_path(r'^orders/(?P<pk>\d+)/edit/$', views.OrderUpdateView.as_view(), name='order_edit'),
    path('orders/<int:pk>/delete', views.OrderDeleteView.as_view(), name='order_delete'),
    re_path(r'^orders/(?P<pk>\d+)/delete/$', views.OrderDeleteView.as_view(), name='order_delete'),

    # ----- 商品管理 -----
    path('goods', views.GoodsListView.as_view(), name='goods_list'),
    re_path(r'^goods/$', views.GoodsListView.as_view(), name='goods_list'),
    path('goods/add', views.GoodsCreateView.as_view(), name='goods_add'),
    re_path(r'^goods/add/$', views.GoodsCreateView.as_view(), name='goods_add'),
    path('goods/<int:pk>/edit', views.GoodsUpdateView.as_view(), name='goods_edit'),
    re_path(r'^goods/(?P<pk>\d+)/edit/$', views.GoodsUpdateView.as_view(), name='goods_edit'),
    path('goods/<int:pk>/delete', views.GoodsDeleteView.as_view(), name='goods_delete'),
    re_path(r'^goods/(?P<pk>\d+)/delete/$', views.GoodsDeleteView.as_view(), name='goods_delete'),

    # ----- 顾客管理 -----
    path('customers', views.CustomerListView.as_view(), name='customer_list'),
    re_path(r'^customers/$', views.CustomerListView.as_view(), name='customer_list'),
    path('customers/add', views.CustomerCreateView.as_view(), name='customer_add'),
    re_path(r'^customers/add/$', views.CustomerCreateView.as_view(), name='customer_add'),
    path('customers/<int:pk>/edit', views.CustomerUpdateView.as_view(), name='customer_edit'),
    re_path(r'^customers/(?P<pk>\d+)/edit/$', views.CustomerUpdateView.as_view(), name='customer_edit'),
    path('customers/<int:pk>/delete', views.CustomerDeleteView.as_view(), name='customer_delete'),
    re_path(r'^customers/(?P<pk>\d+)/delete/$', views.CustomerDeleteView.as_view(), name='customer_delete'),

    # ----- API -----
    path('api/calc-price', views.CalcPriceAPI.as_view(), name='calc_price'),
    re_path(r'^api/calc-price/$', views.CalcPriceAPI.as_view(), name='calc_price'),
    path('api/orders/batch-delete', views.OrderBatchDeleteView.as_view(), name='order_batch_delete'),
    re_path(r'^api/orders/batch-delete/$', views.OrderBatchDeleteView.as_view(), name='order_batch_delete'),
    path('api/orders/batch-status', views.OrderBatchStatusView.as_view(), name='order_batch_status'),
    re_path(r'^api/orders/batch-status/$', views.OrderBatchStatusView.as_view(), name='order_batch_status'),
    path('api/customers/batch-delete', views.CustomerBatchDeleteView.as_view(), name='customer_batch_delete'),
    re_path(r'^api/customers/batch-delete/$', views.CustomerBatchDeleteView.as_view(), name='customer_batch_delete'),

    # ----- 数据导出 -----
    path('export/orders', views.ExportOrdersView.as_view(), name='export_orders'),
    re_path(r'^export/orders/$', views.ExportOrdersView.as_view(), name='export_orders'),
    path('export/accountbooks', views.ExportAccountBooksView.as_view(), name='export_accountbooks'),
    re_path(r'^export/accountbooks/$', views.ExportAccountBooksView.as_view(), name='export_accountbooks'),
    path('settings/theme', views.ThemeSwitchView.as_view(), name='switch_theme'),
    re_path(r'^settings/theme/$', views.ThemeSwitchView.as_view(), name='switch_theme'),

    # ----- 工具/调试 -----
    path('debug/namespace', views.NamespaceInfoView.as_view(), name='namespace'),
    re_path(r'^debug/namespace/$', views.NamespaceInfoView.as_view(), name='namespace'),
    path('hello/', views.HelloView.as_view(), name='hello'),
    path('work', views.WorkView.as_view(), name='work'),
    re_path(r'^work/$', views.WorkView.as_view(), name='work'),
    path('404', views.Page404View.as_view(), name='page404'),
    re_path(r'^404/$', views.Page404View.as_view(), name='page404'),
    path('list', views.RedirectToLoginView.as_view(), name='show_list'),
    re_path(r'^list/$', views.RedirectToLoginView.as_view(), name='show_list'),
]

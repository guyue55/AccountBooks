"""AccountBooks URL Configuration.

路由配置模块，包含以下功能组：
- 认证：登录 / 注册 / 退出
- Dashboard：首页总览
- 交易记录：CRUD 操作
- 商品管理：CRUD 操作
- 顾客管理：CRUD 操作
- API：价格计算接口
- 管理后台：Django Admin
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # ----- 管理后台 -----
    path("admin/", admin.site.urls),
    # ----- 业务路由 (包含 Dashboard, Auth, CRUD) -----
    # 直接包含 accounts.urls，不加前缀，保持原有 URL 结构不变
    path("", include("accounts.urls")),
]

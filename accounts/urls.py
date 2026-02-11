from django.urls import path
from . import views

# app名称，与主urls中的include('accounts.urls')相映射
app_name = "accounts"

urlpatterns = [
    path('', views.NamespaceInfoView.as_view(), name='namespace'),
    path('hello/', views.HelloView.as_view(), name='hello'),
    path('404', views.Page404View.as_view(), name='page404'),
]

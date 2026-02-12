"""
AccountBooks 视图模块。

按功能分组：
1. 通用工具视图 (Hello, Work, 404, 根重定向)
2. 认证视图 (Login, Register, Logout)
3. Dashboard 视图
4. 交易记录 CRUD
5. 商品管理 CRUD
6. 顾客管理 CRUD
7. API 视图 (价格计算)

所有 CRUD 视图均继承 AjaxFormMixin，支持：
- GET 普通请求 → 返回完整页面
- GET AJAX 请求 → 返回 partial 片段（Modal 弹窗内容）
- POST AJAX 请求 → 成功返回 JSON / 失败返回带错误的片段
"""

import json
from decimal import Decimal

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Sum, Count
from django.http import HttpResponse, Http404, JsonResponse
from django.shortcuts import render, redirect, reverse
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, TemplateView, CreateView, UpdateView, DeleteView

from .forms import (
    OrderForm, OrderItemFormSet,
    GoodsInfoForm, AccountInfoForm,
)
from .models import AccountBooks, AccountInfo, GoodsInfo, Order, OrderItem


# ===========================================================================
# 通用工具视图
# ===========================================================================

class HelloView(View):
    """一个简单的入门测试视图。"""
    def get(self, request, *args, **kwargs):
        return HttpResponse("<h1>Hello World！</h1>")


class WorkView(View):
    """默认工作页面视图。"""
    def get(self, request, *args, **kwargs):
        return HttpResponse("<h1>System is Running!</h1>")


class Page404View(View):
    """自定义 404 错误触发视图。"""
    def get(self, request, *args, **kwargs):
        raise Http404("该页面不存在。维护人员暂时不在线，请稍后再试。")


class RedirectToLoginView(View):
    """将旧 /list 路由重定向到登录页。"""
    def get(self, request, *args, **kwargs):
        return redirect(reverse('login'))


class NamespaceInfoView(View):
    """调试用：展示当前请求的命名空间信息。"""
    def get(self, request, *args, **kwargs):
        current_namespace = request.resolver_match.namespace
        return HttpResponse(f"<h1>命名空间 (Namespace): {current_namespace}</h1>")


# ===========================================================================
# 认证视图
# ===========================================================================

class LoginView(TemplateView):
    """登录页面视图。"""
    template_name = "login-meihua.html"

    def post(self, request, *args, **kwargs):
        """处理登录表单提交。"""
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.GET.get('next', 'index')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(next_url)
        else:
            return render(request, self.template_name, {
                'error': '用户名或密码错误，请重试。',
                'username': username
            })


class RegisterView(TemplateView):
    """注册页面视图。"""
    template_name = "register.html"

    def post(self, request, *args, **kwargs):
        """处理注册表单提交，含密码一致性校验和用户名唯一性校验。"""
        username = request.POST.get('username')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        if password != password_confirm:
            return render(request, self.template_name, {'error': '两次输入的密码不一致。'})
        if User.objects.filter(username=username).exists():
            return render(request, self.template_name, {'error': '该用户名已被注册。'})
        user = User.objects.create_user(username=username, password=password)
        login(request, user)
        return redirect('index')


class LogoutView(View):
    """退出登录视图 —— 登出并重定向到登录页。"""
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect('login')


# ===========================================================================
# AJAX 表单 Mixin
# ===========================================================================

class AjaxFormMixin:
    """AJAX 表单响应 Mixin —— 所有弹窗表单视图的基类。

    行为：
    - GET AJAX → 返回 partial 模板（仅弹窗内容，无 <html> 外壳）
    - POST 成功 + AJAX → 返回 JSON { success: true, message: '...' }
    - POST 失败 + AJAX → 重新渲染 partial 模板（含错误信息）
    - 非 AJAX 请求 → 走 Django 默认行为
    """
    partial_template_name = None  # 子类覆盖：弹窗片段模板路径
    success_message = '操作成功'   # 子类可覆盖成功消息

    def _is_ajax(self, request):
        """判断请求是否为 AJAX。"""
        return request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    def get(self, request, *args, **kwargs):
        """GET 请求：AJAX 返回片段，普通返回完整页面。"""
        if self._is_ajax(request) and self.partial_template_name:
            # 构建上下文并渲染片段
            self.object = self.get_object() if hasattr(self, 'get_object') and 'pk' in kwargs else None
            form = self.get_form()
            context = self.get_context_data(form=form)
            return render(request, self.partial_template_name, context)
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        """表单校验通过：保存并返回成功响应。"""
        self.object = form.save()
        if self._is_ajax(self.request):
            return JsonResponse({
                'success': True,
                'message': self.success_message,
                'id': self.object.pk,
                'text': str(self.object),
            })
        return super().form_valid(form)

    def form_invalid(self, form):
        """表单校验失败：AJAX 时返回含错误信息的片段。"""
        if self._is_ajax(self.request):
            context = self.get_context_data(form=form)
            return render(self.request, self.partial_template_name, context)
        return super().form_invalid(form)


# ===========================================================================
# Dashboard 视图
# ===========================================================================

class DashboardView(LoginRequiredMixin, ListView):
    """系统仪表盘 —— 展示账簿总览和关键统计数据。"""
    model = AccountBooks
    template_name = "index.html"
    context_object_name = "books"
    login_url = "/login"

    def get_context_data(self, **kwargs):
        """注入统计聚合数据和活跃导航标记。"""
        context = super().get_context_data(**kwargs)
        aggregates = AccountBooks.objects.aggregate(
            total_wait=Sum('money_wait'),
            total_over=Sum('money_over'),
            total_default=Sum('money_default'),
        )
        order_stats = Order.objects.aggregate(
            total_count=Count('id'),
            total_revenue=Sum('total_price'),
        )
        # 计算收款率（已收/应收）
        total_revenue = order_stats.get('total_revenue') or Decimal('0')
        total_over = aggregates.get('total_over') or Decimal('0')
        collection_rate = (
            round(total_over / total_revenue * 100, 1)
            if total_revenue > 0 else 0
        )
        context.update({
            'active_nav': 'dashboard',
            'total_wait': aggregates.get('total_wait') or 0,
            'total_over': aggregates.get('total_over') or 0,
            'total_default': aggregates.get('total_default') or 0,
            'order_count': order_stats.get('total_count') or 0,
            'collection_rate': collection_rate,
        })
        return context


# ===========================================================================
# 交易记录 CRUD
# ===========================================================================

class OrdersView(LoginRequiredMixin, ListView):
    """交易记录列表视图。"""
    model = Order
    template_name = "orders.html"
    context_object_name = "orders"
    login_url = "/login"
    paginate_by = 10

    def get_queryset(self):
        """优化查询并支持多维筛选。"""
        from django.db.models import Q
        
        qs = Order.objects.select_related('account').prefetch_related('items__goods').order_by('-buy_time')
        
        # 1. 搜索词筛选 (顾客姓名或商品名)
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(
                Q(account__name__icontains=q) | 
                Q(items__goods__goods__icontains=q)
            ).distinct()
            
        # 2. 状态筛选
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
            
        # 3. 日期范围筛选
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        if start_date:
            qs = qs.filter(buy_time__date__gte=start_date)
        if end_date:
            qs = qs.filter(buy_time__date__lte=end_date)
            
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_nav'] = 'orders'
        # 保持分页时的筛选参数
        query_params = self.request.GET.copy()
        if 'page' in query_params:
            del query_params['page']
        context['query_string'] = query_params.urlencode()
        return context


class OrderCreateView(LoginRequiredMixin, AjaxFormMixin, CreateView):
    """新增交易记录视图（含 OrderItem formset）。"""
    model = Order
    form_class = OrderForm
    template_name = "orders.html"  # 非 AJAX 回退
    partial_template_name = "partials/order_form.html"
    success_url = reverse_lazy('orders')
    success_message = '交易记录创建成功'
    login_url = "/login"

    def get(self, request, *args, **kwargs):
        """GET：返回订单表单和空的行项 formset。"""
        self.object = None
        if self._is_ajax(request):
            form = self.get_form()
            formset = OrderItemFormSet()
            context = self.get_context_data(form=form, formset=formset, title='新增交易记录')
            return render(request, self.partial_template_name, context)
        return redirect('orders')

    def post(self, request, *args, **kwargs):
        """POST：同时处理订单头和行项 formset。"""
        self.object = None
        form = self.get_form()
        formset = OrderItemFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            return self._save_order(form, formset)
        return self._render_errors(form, formset)

    def _save_order(self, form, formset):
        """保存订单头和行项，计算总价。"""
        with transaction.atomic():
            order = form.save()
            formset.instance = order
            items = formset.save()
            # 重新计算总价
            order.calc_total()
        
        if self._is_ajax(self.request):
            return JsonResponse({
                'success': True,
                'message': self.success_message,
                'id': order.pk,
            })
        return redirect(self.success_url)

    def _render_errors(self, form, formset):
        """表单校验失败时重新渲染。"""
        context = self.get_context_data(form=form, formset=formset, title='新增交易记录')
        if self._is_ajax(self.request):
            return render(self.request, self.partial_template_name, context)
        return render(self.request, self.template_name, context)


class OrderUpdateView(LoginRequiredMixin, AjaxFormMixin, UpdateView):
    """编辑交易记录视图。"""
    model = Order
    form_class = OrderForm
    template_name = "orders.html"
    partial_template_name = "partials/order_form.html"
    success_url = reverse_lazy('orders')
    success_message = '交易记录更新成功'
    login_url = "/login"

    def get(self, request, *args, **kwargs):
        """GET：返回预填充的订单表单和行项 formset。"""
        self.object = self.get_object()
        if self._is_ajax(request):
            form = self.get_form()
            formset = OrderItemFormSet(instance=self.object)
            context = self.get_context_data(
                form=form, formset=formset,
                title='编辑交易记录', is_edit=True,
            )
            return render(request, self.partial_template_name, context)
        return redirect('orders')

    def post(self, request, *args, **kwargs):
        """POST：同时处理订单头和行项 formset。"""
        self.object = self.get_object()
        form = self.get_form()
        formset = OrderItemFormSet(request.POST, instance=self.object)

        if form.is_valid() and formset.is_valid():
            return self._save_order(form, formset)
        return self._render_errors(form, formset)

    def _save_order(self, form, formset):
        """保存更新并重新计算总价。"""
        with transaction.atomic():
            order = form.save()
            formset.save()
            order.calc_total()
        
        if self._is_ajax(self.request):
            return JsonResponse({
                'success': True,
                'message': self.success_message,
                'id': order.pk,
            })
        return redirect(self.success_url)

    def _render_errors(self, form, formset):
        """表单校验失败时重新渲染。"""
        context = self.get_context_data(
            form=form, formset=formset,
            title='编辑交易记录', is_edit=True,
        )
        if self._is_ajax(self.request):
            return render(self.request, self.partial_template_name, context)
        return render(self.request, self.template_name, context)


class OrderDeleteView(LoginRequiredMixin, DeleteView):
    """删除交易记录视图 —— 支持 AJAX POST 删除。"""
    model = Order
    success_url = reverse_lazy('orders')
    login_url = "/login"

    def post(self, request, *args, **kwargs):
        """POST 删除并返回 JSON（AJAX）或重定向。"""
        self.object = self.get_object()
        self.object.delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': '交易记录已删除'})
        return redirect(self.success_url)

    def get(self, request, *args, **kwargs):
        """GET 直接执行删除（简化流程）。"""
        return self.post(request, *args, **kwargs)


# ===========================================================================
# 商品管理 CRUD
# ===========================================================================

class GoodsListView(LoginRequiredMixin, ListView):
    """商品列表视图。"""
    model = GoodsInfo
    template_name = "goods.html"
    context_object_name = "goods_list"
    login_url = "/login"
    paginate_by = 15

    def get_queryset(self):
        qs = super().get_queryset().order_by('-updated')
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(goods__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_nav'] = 'goods'
        # 保持分页时的筛选参数
        query_params = self.request.GET.copy()
        if 'page' in query_params:
            del query_params['page']
        context['query_string'] = query_params.urlencode()
        return context


class GoodsCreateView(LoginRequiredMixin, AjaxFormMixin, CreateView):
    """新增商品视图。"""
    model = GoodsInfo
    form_class = GoodsInfoForm
    template_name = "goods.html"
    partial_template_name = "partials/goods_form.html"
    success_url = reverse_lazy('goods_list')
    success_message = '商品创建成功'
    login_url = "/login"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '新增商品'
        return context


class GoodsUpdateView(LoginRequiredMixin, AjaxFormMixin, UpdateView):
    """编辑商品视图。"""
    model = GoodsInfo
    form_class = GoodsInfoForm
    template_name = "goods.html"
    partial_template_name = "partials/goods_form.html"
    success_url = reverse_lazy('goods_list')
    success_message = '商品更新成功'
    login_url = "/login"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '编辑商品'
        context['is_edit'] = True
        return context


class GoodsDeleteView(LoginRequiredMixin, DeleteView):
    """删除商品视图。"""
    model = GoodsInfo
    success_url = reverse_lazy('goods_list')
    login_url = "/login"

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            self.object.delete()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': '商品已删除'})
        except Exception:
            # 商品被 OrderItem 引用时无法删除 (PROTECT)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': '该商品已被订单引用，无法删除'
                }, status=400)
        return redirect(self.success_url)

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


# ===========================================================================
# 顾客管理 CRUD
# ===========================================================================

class CustomerListView(LoginRequiredMixin, ListView):
    """顾客列表视图。"""
    model = AccountInfo
    template_name = "customers.html"
    context_object_name = "customers"
    login_url = "/login"
    paginate_by = 15

    def get_queryset(self):
        from django.db.models import Q
        qs = super().get_queryset().order_by('-updated')
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(
                Q(name__icontains=q) |
                Q(real_name__icontains=q) |
                Q(location__icontains=q) |
                Q(remarks__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_nav'] = 'customers'
        # 保持分页时的筛选参数
        query_params = self.request.GET.copy()
        if 'page' in query_params:
            del query_params['page']
        context['query_string'] = query_params.urlencode()
        return context


class CustomerCreateView(LoginRequiredMixin, AjaxFormMixin, CreateView):
    """新增顾客视图。"""
    model = AccountInfo
    form_class = AccountInfoForm
    template_name = "customers.html"
    partial_template_name = "partials/customer_form.html"
    success_url = reverse_lazy('customer_list')
    success_message = '顾客创建成功'
    login_url = "/login"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '新增顾客'
        return context


class CustomerUpdateView(LoginRequiredMixin, AjaxFormMixin, UpdateView):
    """编辑顾客视图。"""
    model = AccountInfo
    form_class = AccountInfoForm
    template_name = "customers.html"
    partial_template_name = "partials/customer_form.html"
    success_url = reverse_lazy('customer_list')
    success_message = '顾客信息更新成功'
    login_url = "/login"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '编辑顾客'
        context['is_edit'] = True
        return context


class CustomerDeleteView(LoginRequiredMixin, DeleteView):
    """删除顾客视图。"""
    model = AccountInfo
    success_url = reverse_lazy('customer_list')
    login_url = "/login"

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            self.object.delete()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': '顾客已删除'})
        except Exception:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': '该顾客有关联订单，无法删除'
                }, status=400)
        return redirect(self.success_url)

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


# ===========================================================================
# API 视图
# ===========================================================================

class CalcPriceAPI(LoginRequiredMixin, View):
    """价格计算 API —— 前端传入商品 ID 和数量，返回单价和小计。

    请求格式 (POST JSON):
        { "items": [{ "goods_id": 1, "quantity": 2 }, ...] }

    响应格式:
        { "items": [{ "goods_id": 1, "unit_price": "88.00", "subtotal": "176.00" }, ...],
          "total": "176.00" }
    """
    login_url = "/login"

    def post(self, request, *args, **kwargs):
        """处理价格计算请求。"""
        try:
            data = json.loads(request.body)
            items = data.get('items', [])
        except (json.JSONDecodeError, AttributeError):
            return JsonResponse({'error': '请求数据格式错误'}, status=400)

        result_items = []
        total = Decimal('0.00')

        for item in items:
            goods_id = item.get('goods_id')
            try:
                quantity = int(item.get('quantity', 1))
                if quantity <= 0:
                    raise ValueError("数量必须大于0")
            except (ValueError, TypeError):
                # 如果数量无效，默认按 0 处理，或者返回错误
                quantity = 0

            try:
                goods = GoodsInfo.objects.get(pk=goods_id)
                subtotal = goods.goods_price * quantity
                total += subtotal
                result_items.append({
                    'goods_id': goods_id,
                    'unit_price': str(goods.goods_price),
                    'subtotal': str(subtotal),
                })
            except GoodsInfo.DoesNotExist:
                result_items.append({
                    'goods_id': goods_id,
                    'unit_price': '0.00',
                    'subtotal': '0.00',
                })

        return JsonResponse({
            'items': result_items,
            'total': str(total),
        })

    def get(self, request, *args, **kwargs):
        """GET 请求返回单个商品的单价，用于 OrderItem 行选择商品时实时获取。"""
        goods_id = request.GET.get('goods_id')
        if goods_id:
            try:
                goods = GoodsInfo.objects.get(pk=goods_id)
                return JsonResponse({'unit_price': str(goods.goods_price)})
            except GoodsInfo.DoesNotExist:
                pass
        return JsonResponse({'unit_price': '0.00'})

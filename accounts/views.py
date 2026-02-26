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
import logging
from decimal import Decimal

logger = logging.getLogger('accounts')

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Sum, Count
from django.http import HttpResponse, Http404, JsonResponse
from django.shortcuts import render, redirect, reverse
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, TemplateView, CreateView, UpdateView, DeleteView

from .forms import (
    OrderForm, OrderItemFormSet,
    GoodsInfoForm, AccountInfoForm,
)
from .models import AccountBooks, AccountInfo, GoodsInfo, Order, OrderItem, UserProfile


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
                'id': self.object.pk if self.object else None,
                'text': str(self.object),
            })
        logger.info(f"User {self.request.user} saved {self.model.__name__} {self.object.pk if self.object else 'new'}")
        return super().form_valid(form)

    def form_invalid(self, form):
        """表单校验失败：AJAX 时返回含错误信息的片段。"""
        if self._is_ajax(self.request):
            context = self.get_context_data(form=form)
            logger.warning(f"User {self.request.user} failed to save {self.model.__name__} due to form errors.")
            return render(self.request, self.partial_template_name, context)
        logger.warning(f"User {self.request.user} failed to save {self.model.__name__} (non-AJAX) due to form errors.")
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
        
        # 1. 图表数据：最近 7 天的收入趋势
        today = timezone.now().date()
        date_list = [(today - timezone.timedelta(days=i)) for i in range(6, -1, -1)]
        revenue_trend_dates = [d.strftime('%m-%d') for d in date_list]
        revenue_trend_data = []
        for d in date_list:
            daily_orders = Order.objects.filter(buy_time__date=d)
            daily_sum = daily_orders.aggregate(total=Sum('total_price'))['total'] or 0
            revenue_trend_data.append(float(daily_sum))
            
        # 2. 图表数据：欠款客户分布 (取前 5 名欠款最多的，其余归为"其他")
        debt_books = AccountBooks.objects.filter(money_wait__gt=0).order_by('-money_wait')
        debt_distribution = []
        if debt_books.count() > 5:
            top_5 = debt_books[:5]
            others = debt_books[5:]
            for b in top_5:
                debt_distribution.append({'name': b.account_info.name, 'value': float(b.money_wait)})
            others_sum = others.aggregate(total=Sum('money_wait'))['total'] or 0
            if others_sum > 0:
                debt_distribution.append({'name': '其他客户', 'value': float(others_sum)})
        else:
            for b in debt_books:
                debt_distribution.append({'name': b.account_info.name, 'value': float(b.money_wait)})

        context.update({
            'active_nav': 'dashboard',
            'total_wait': aggregates.get('total_wait') or 0,
            'total_over': aggregates.get('total_over') or 0,
            'total_default': aggregates.get('total_default') or 0,
            'order_count': order_stats.get('total_count') or 0,
            'collection_rate': collection_rate,
            
            # 图表所需 JSON 数据
            'chart_revenue_dates': json.dumps(revenue_trend_dates),
            'chart_revenue_data': json.dumps(revenue_trend_data),
            'chart_debt_data': json.dumps(debt_distribution, ensure_ascii=False),
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
            logger.info(f"User {self.request.user} created Order {order.pk} with total {order.total_price_real}")
        
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
            logger.info(f"User {self.request.user} updated Order {order.pk} with total {order.total_price_real}")
        
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
        logger.info(f"User {request.user} deleted Order {self.object.pk}")
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
        
        # 手动检查商品是否被非软删除的 OrderItem 引用
        if OrderItem.objects.filter(goods=self.object).exists():
            logger.warning(f"User {request.user} failed to delete Goods {self.object.pk}: Linked to active OrderItems")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': '该商品已被订单引用，无法直接删除（请先删除对应订单）。'
                }, status=400)

        try:
            logger.info(f"User {request.user} soft-deleted Goods {self.object.pk}")
            self.object.delete()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': '商品已删除'})
        except Exception as e:
            logger.error(f"User {request.user} failed to soft-delete Goods {self.object.pk}: {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': f'删除失败: {str(e)}'}, status=500)
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

        # 手动检查该顾客是否有关联的活动（未软删除）订单
        if Order.objects.filter(account=self.object).exists():
            logger.warning(f"User {request.user} failed to delete Customer {self.object.pk}: Linked to active Orders")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': '该顾客有关联订单，无法直接删除（请先删除关联订单）。'
                }, status=400)

        try:
            logger.info(f"User {request.user} soft-deleted Customer {self.object.pk}")
            self.object.delete()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': '顾客已删除'})
        except Exception as e:
            logger.error(f"User {request.user} failed to soft-delete Customer {self.object.pk}: {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': f'删除失败: {str(e)}'}, status=500)
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

        for idx, item in enumerate(items):
            goods_id = item.get('goods_id')
            try:
                quantity = int(item.get('quantity', 1))
                if quantity <= 0:
                    return JsonResponse(
                        {'error': '数量必须大于0', 'index': idx, 'goods_id': goods_id},
                        status=400,
                    )
            except (ValueError, TypeError):
                return JsonResponse(
                    {'error': '数量必须为正整数', 'index': idx, 'goods_id': goods_id},
                    status=400,
                )

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


# ===========================================================================
# 批量操作 API
# ===========================================================================

class OrderBatchDeleteView(LoginRequiredMixin, View):
    """批量删除交易记录"""
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            ids = data.get('ids', [])
            if not ids:
                return JsonResponse({'success': False, 'message': '未选择任何记录'}, status=400)
            
            deleted_count, _ = Order.objects.filter(id__in=ids).delete()
            logger.info(f"User {request.user} batch deleted {deleted_count} Orders")
            return JsonResponse({'success': True, 'message': f'成功删除 {deleted_count} 条记录'})
        except Exception as e:
            logger.error(f"User {request.user} batch delete Orders failed: {str(e)}")
            return JsonResponse({'success': False, 'message': f'批量删除失败: {str(e)}'}, status=500)

class OrderBatchStatusView(LoginRequiredMixin, View):
    """批量修改交易记录还款状态"""
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            ids = data.get('ids', [])
            status = data.get('status')
            
            if not ids or not status:
                return JsonResponse({'success': False, 'message': '参数错误'}, status=400)
                
            updated_count = Order.objects.filter(id__in=ids).update(status=status)
            
            # 手动触发账簿汇总更新，因为 bulk_update 无法触发 post_save Signal
            affected_accounts = AccountInfo.objects.filter(order__in=ids).distinct()
            for account in affected_accounts:
                AccountBooks.objects.get(account_info=account).update_summary()
            
            logger.info(f"User {request.user} batch updated {updated_count} Orders to status '{status}'")
            return JsonResponse({'success': True, 'message': f'成功更新 {updated_count} 条记录状态'})
        except Exception as e:
            logger.error(f"User {request.user} batch update Orders status failed: {str(e)}")
            return JsonResponse({'success': False, 'message': f'批量更新失败: {str(e)}'}, status=500)

class CustomerBatchDeleteView(LoginRequiredMixin, View):
    """批量软删除顾客记录。"""
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            ids = data.get('ids', [])
            if not ids:
                return JsonResponse({'success': False, 'message': '未选择任何记录'}, status=400)

            # 手动检查是否有顾客还关联着未删除的订单
            # （逻辑删除不触发数据库 ProtectedError，需在代码层自行拦截）
            blocked = AccountInfo.objects.filter(
                id__in=ids, order__is_deleted=False
            ).distinct()
            if blocked.exists():
                names = '、'.join(blocked.values_list('name', flat=True))
                logger.warning(
                    f"User {request.user} tried to delete Customers with active orders: {names}"
                )
                return JsonResponse(
                    {'success': False, 'message': f'以下顾客存在未删除的关联订单，无法直接删除：{names}'},
                    status=400
                )

            deleted_count, _ = AccountInfo.objects.filter(id__in=ids).delete()
            logger.info(f"User {request.user} batch soft-deleted {deleted_count} Customers")
            return JsonResponse({'success': True, 'message': f'成功删除 {deleted_count} 名顾客'})
        except Exception as e:
            logger.error(f"User {request.user} batch delete Customers failed: {str(e)}")
            return JsonResponse({'success': False, 'message': f'批量删除失败: {str(e)}'}, status=500)


# ===========================================================================
# 数据导出视图 (CSV)
# ===========================================================================

import csv

class ExportOrdersView(LoginRequiredMixin, View):
    """导出交易记录为 CSV 文件。"""
    login_url = "/login"

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="orders_export.csv"'
        response.write(b'\xef\xbb\xbf')  # 写入 BOM, 防止 Excel 乱码

        writer = csv.writer(response)
        writer.writerow(['订单ID', '顾客姓名', '商品明细', '应收总价', '实收总价', '状态', '购买时间'])

        orders = Order.objects.select_related('account').prefetch_related('items__goods').order_by('-buy_time')
        for order in orders:
            items_desc = " | ".join([f"{item.goods.goods}x{item.quantity}" for item in order.items.all()])
            writer.writerow([
                order.id,
                order.account.name,
                items_desc,
                order.total_price,
                order.total_price_real,
                order.get_status_display(),
                timezone.localtime(order.buy_time).strftime('%Y-%m-%d %H:%M:%S')
            ])
            
        return response

class ExportAccountBooksView(LoginRequiredMixin, View):
    """导出账务汇总为 CSV 文件。"""
    login_url = "/login"

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="accountbooks_export.csv"'
        response.write(b'\xef\xbb\xbf')  # 写入 BOM

        writer = csv.writer(response)
        writer.writerow(['债务人', '联系地址', '累计应收', '当前待还', '已还金额', '赖账金额', '最后更新时间'])

        books = AccountBooks.objects.select_related('account_info').order_by('-money_wait')
        for book in books:
            writer.writerow([
                book.account_info.name,
                book.account_info.location,
                book.money_total,
                book.money_wait,
                book.money_over,
                book.money_default,
                timezone.localtime(book.updated).strftime('%Y-%m-%d %H:%M:%S')
            ])
            
        return response

class ThemeSwitchView(LoginRequiredMixin, View):
    """处理用户切换主题的 AJAX 请求。"""
    def post(self, request, *args, **kwargs):
        theme = request.POST.get('theme')
        if theme in ['dark', 'light', 'nord', 'purple']:
            # 使用 get_or_create 确保 profile 存在
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            profile.theme = theme
            profile.save()
            return JsonResponse({'status': 'ok', 'theme': theme})
        return JsonResponse({'status': 'error', 'message': 'Invalid theme'}, status=400)

"""
AccountBooks 表单模块。

提供三组核心业务表单：
- GoodsInfoForm: 商品新增/编辑
- AccountInfoForm: 购买人新增/编辑
- OrderForm: 订单头信息
- OrderItemForm + OrderItemFormSet: 订单行项（商品×数量）

所有表单统一使用 'form-input' CSS 类，以适配全局暗色主题样式。
"""

from django import forms
from django.forms import inlineformset_factory

from .models import Order, OrderItem, AccountInfo, GoodsInfo


class GoodsInfoForm(forms.ModelForm):
    """商品信息表单 —— 商品新增/编辑复用。"""

    class Meta:
        model = GoodsInfo
        fields = ['goods', 'goods_price']
        widgets = {
            'goods': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '请输入商品名称',
            }),
            'goods_price': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0',
            }),
        }


class AccountInfoForm(forms.ModelForm):
    """购买人信息表单 —— 购买人新增/编辑复用。"""

    class Meta:
        model = AccountInfo
        fields = ['name', 'real_name', 'age', 'location', 'remarks']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '请输入名称',
            }),
            'real_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '请输入真实姓名',
            }),
            'age': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': '0',
                'min': '0',
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '请输入地址',
            }),
            'remarks': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': '选填备注信息',
                'rows': 3,
            }),
        }


class OrderForm(forms.ModelForm):
    """订单头信息表单。

    仅包含购买人、实收金额和还款状态字段。
    应收金额由 OrderItem 行项自动合计，不在此表单中暴露。
    """

    class Meta:
        model = Order
        fields = ['account', 'total_price_real', 'status']
        widgets = {
            'account': forms.Select(attrs={'class': 'form-input'}),
            'total_price_real': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0',
            }),
            'status': forms.Select(attrs={'class': 'form-input'}),
        }


class OrderItemForm(forms.ModelForm):
    """订单行项表单 —— 用于 formset 中管理每个商品的数量。

    unit_price 设为 readonly，前端通过 JS 自动填充当前商品单价。
    """

    class Meta:
        model = OrderItem
        fields = ['goods', 'quantity', 'unit_price']
        widgets = {
            'goods': forms.Select(attrs={'class': 'form-input'}),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': '1',
                'value': '1',
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-input',
                'readonly': 'readonly',
                'step': '0.01',
            }),
        }


# 订单行项 Formset —— 内联管理订单下的所有商品行
# extra=1 表示默认显示一个空行，can_delete=True 支持删除行
OrderItemFormSet = inlineformset_factory(
    Order,
    OrderItem,
    form=OrderItemForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False,
)

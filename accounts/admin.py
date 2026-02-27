"""AccountBooks Admin 后台配置模块。.

注册所有业务模型到 Django Admin，提供：
- 列表显示字段
- 搜索与过滤
- 内联编辑（OrderItem）
- 自定义管理动作
"""

from django.contrib import admin

from .models import AccountBooks, AccountInfo, GoodsInfo, Order, OrderItem


@admin.register(AccountInfo)
class AccountInfoAdmin(admin.ModelAdmin):
    """债务人详细信息管理。."""

    list_display = ("name", "real_name", "age", "location", "updated")
    list_filter = ("location",)
    search_fields = ("name", "real_name", "location")


@admin.register(GoodsInfo)
class GoodsInfoAdmin(admin.ModelAdmin):
    """商品及其价格管理。."""

    list_display = ("goods", "goods_price", "updated")
    search_fields = ("goods",)


class OrderItemInline(admin.TabularInline):
    """在订单 Admin 中内联编辑行项。."""

    model = OrderItem
    extra = 1
    readonly_fields = ("subtotal",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """交易订单管理。."""

    list_display = (
        "id",
        "account",
        "goods_display",
        "total_price",
        "status",
        "buy_time",
    )
    list_filter = ("status", "buy_time", "account")
    search_fields = ("account__name", "account__real_name")
    date_hierarchy = "buy_time"
    inlines = [OrderItemInline]

    def goods_display(self, obj):
        """在列表页显示关联的商品名称（从 OrderItem 获取）。."""
        return ", ".join([item.goods.goods for item in obj.items.all()])

    goods_display.short_description = "包含商品"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """订单行项管理。."""

    list_display = ("order", "goods", "quantity", "unit_price", "subtotal")
    list_filter = ("goods",)
    search_fields = ("order__account__name", "goods__goods")


@admin.register(AccountBooks)
class AccountBooksAdmin(admin.ModelAdmin):
    """账簿汇总总览。."""

    list_display = (
        "account_info",
        "money_wait",
        "money_over",
        "money_default",
        "updated",
    )
    list_filter = ("updated",)
    search_fields = ("account_info__name",)

    actions = ["recalculate_summary"]

    def recalculate_summary(self, request, queryset):
        """手动触发重新计算选中记录的汇总数据。."""
        for book in queryset:
            book.update_summary()
        self.message_user(request, "选中的账簿已重新计算汇总。")

    recalculate_summary.short_description = "重新计算选中账簿"

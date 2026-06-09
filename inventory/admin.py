from django.contrib import admin, messages
from django.core.exceptions import ValidationError

from .models import StockBatch, StockMovement


@admin.register(StockBatch)
class StockBatchAdmin(admin.ModelAdmin):
    list_display = (
        "batch_no",
        "item_type_display",
        "item_code_display",
        "item_name_display",
        "warehouse",
        "quantity",
        "unit",
        "supplier",
        "is_active",
        "created_at",
    )
    list_filter = (
        "warehouse",
        "is_active",
        "created_at",
    )
    search_fields = (
        "batch_no",
        "material__code",
        "material__name",
        "product__code",
        "product__name",
        "supplier__name",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
    )
    ordering = ("-created_at",)

    fieldsets = (
        (
            "库存对象",
            {
                "fields": (
                    "material",
                    "product",
                    "warehouse",
                    "batch_no",
                    "supplier",
                )
            },
        ),
        (
            "库存数量",
            {
                "fields": (
                    "quantity",
                    "unit",
                )
            },
        ),
        (
            "日期信息",
            {
                "fields": (
                    "production_date",
                    "expiry_date",
                )
            },
        ),
        (
            "其他信息",
            {
                "fields": (
                    "note",
                    "is_active",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    @admin.display(description="类型")
    def item_type_display(self, obj):
        return obj.item_type

    @admin.display(description="编号")
    def item_code_display(self, obj):
        return obj.item_code

    @admin.display(description="名称")
    def item_name_display(self, obj):
        return obj.item_name


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "movement_type",
        "stock_batch",
        "quantity",
        "before_quantity",
        "after_quantity",
        "document_no",
        "is_applied",
        "applied_at",
        "created_by",
        "created_at",
    )
    list_filter = (
        "movement_type",
        "is_applied",
        "created_at",
        "applied_at",
    )
    search_fields = (
        "stock_batch__batch_no",
        "stock_batch__material__code",
        "stock_batch__material__name",
        "stock_batch__product__code",
        "stock_batch__product__name",
        "document_no",
        "reason",
    )
    readonly_fields = (
        "before_quantity",
        "after_quantity",
        "is_applied",
        "applied_at",
        "created_by",
        "created_at",
        "updated_at",
    )
    ordering = ("-created_at",)

    actions = [
        "apply_selected_movements",
    ]

    fieldsets = (
        (
            "库存变动",
            {
                "fields": (
                    "stock_batch",
                    "movement_type",
                    "quantity",
                )
            },
        ),
        (
            "来源信息",
            {
                "fields": (
                    "document_no",
                    "reason",
                    "note",
                )
            },
        ),
        (
            "应用结果",
            {
                "fields": (
                    "before_quantity",
                    "after_quantity",
                    "is_applied",
                    "applied_at",
                )
            },
        ),
        (
            "系统信息",
            {
                "fields": (
                    "created_by",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        if not obj.pk and obj.created_by is None:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    @admin.action(description="应用选中的库存流水")
    def apply_selected_movements(self, request, queryset):
        success_count = 0
        error_messages = []

        for movement in queryset:
            try:
                movement.apply()
                success_count += 1
            except ValidationError as exc:
                error_messages.append(f"流水 ID {movement.id}: {exc}")

        if success_count > 0:
            self.message_user(
                request,
                f"成功应用 {success_count} 条库存流水。",
                level=messages.SUCCESS,
            )

        if error_messages:
            self.message_user(
                request,
                "；".join(error_messages),
                level=messages.ERROR,
            )
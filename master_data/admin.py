from django.contrib import admin

from .models import Customer, Supplier, Warehouse, Material, Product


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "contact_person",
        "phone",
        "email",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active",)
    search_fields = ("name", "contact_person", "phone", "email")
    ordering = ("name",)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "contact_person",
        "phone",
        "email",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active",)
    search_fields = ("name", "contact_person", "phone", "email")
    ordering = ("name",)


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "location",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active",)
    search_fields = ("code", "name", "location")
    ordering = ("code",)


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "material_type",
        "supplier",
        "unit",
        "safety_stock",
        "reference_price",
        "currency",
        "is_active",
    )
    list_filter = ("material_type", "currency", "is_active")
    search_fields = ("code", "name", "supplier__name")
    ordering = ("code",)

    fieldsets = (
        (
            "基础信息",
            {
                "fields": (
                    "code",
                    "name",
                    "material_type",
                    "supplier",
                    "unit",
                )
            },
        ),
        (
            "库存与成本",
            {
                "fields": (
                    "safety_stock",
                    "reference_price",
                    "currency",
                )
            },
        ),
        (
            "其他信息",
            {
                "fields": (
                    "note",
                    "is_active",
                )
            },
        ),
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "customer",
        "specification",
        "hardness",
        "color",
        "unit",
        "is_active",
    )
    list_filter = ("is_active", "customer")
    search_fields = ("code", "name", "specification", "customer__name")
    ordering = ("code",)
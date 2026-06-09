from django.db import models


class Customer(models.Model):
    name = models.CharField("客户名称", max_length=100)
    contact_person = models.CharField("联系人", max_length=50, blank=True)
    phone = models.CharField("电话", max_length=30, blank=True)
    email = models.EmailField("邮箱", blank=True)
    address = models.TextField("地址", blank=True)
    note = models.TextField("备注", blank=True)
    is_active = models.BooleanField("启用", default=True)

    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "客户"
        verbose_name_plural = "客户"

    def __str__(self):
        return self.name


class Supplier(models.Model):
    name = models.CharField("供应商名称", max_length=100)
    contact_person = models.CharField("联系人", max_length=50, blank=True)
    phone = models.CharField("电话", max_length=30, blank=True)
    email = models.EmailField("邮箱", blank=True)
    address = models.TextField("地址", blank=True)
    note = models.TextField("备注", blank=True)
    is_active = models.BooleanField("启用", default=True)

    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "供应商"
        verbose_name_plural = "供应商"

    def __str__(self):
        return self.name


class Warehouse(models.Model):
    code = models.CharField("仓库编号", max_length=30, unique=True)
    name = models.CharField("仓库名称", max_length=100)
    location = models.CharField("位置", max_length=200, blank=True)
    note = models.TextField("备注", blank=True)
    is_active = models.BooleanField("启用", default=True)

    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "仓库"
        verbose_name_plural = "仓库"

    def __str__(self):
        return f"{self.code} - {self.name}"


class Material(models.Model):
    MATERIAL_TYPE_CHOICES = [
        ("rubber", "橡胶原料"),
        ("filler", "填料"),
        ("oil", "油料"),
        ("agent", "助剂"),
        ("package", "包装材料"),
        ("other", "其他"),
    ]

    code = models.CharField("物料编号", max_length=50, unique=True)
    name = models.CharField("物料名称", max_length=100)
    material_type = models.CharField("物料类型", max_length=30, choices=MATERIAL_TYPE_CHOICES)

    supplier = models.ForeignKey(
        Supplier,
        verbose_name="默认供应商",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    unit = models.CharField("单位", max_length=20, default="kg")
    safety_stock = models.DecimalField("安全库存", max_digits=12, decimal_places=3, default=0)
    note = models.TextField("备注", blank=True)
    is_active = models.BooleanField("启用", default=True)

    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "物料"
        verbose_name_plural = "物料"

    def __str__(self):
        return f"{self.code} - {self.name}"


class Product(models.Model):
    code = models.CharField("产品编号", max_length=50, unique=True)
    name = models.CharField("产品名称", max_length=100)

    customer = models.ForeignKey(
        Customer,
        verbose_name="客户",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    specification = models.CharField("规格", max_length=200, blank=True)
    hardness = models.CharField("硬度", max_length=50, blank=True)
    color = models.CharField("颜色", max_length=50, blank=True)
    unit = models.CharField("单位", max_length=20, default="pcs")
    note = models.TextField("备注", blank=True)
    is_active = models.BooleanField("启用", default=True)

    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "产品"
        verbose_name_plural = "产品"

    def __str__(self):
        return f"{self.code} - {self.name}"
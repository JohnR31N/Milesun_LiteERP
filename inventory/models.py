from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from master_data.models import Material, Product, Supplier, Warehouse


class StockBatch(models.Model):
    """
    库存批次。

    一个批次可以是：
    1. 原材料批次：material 不为空，product 为空
    2. 成品批次：product 不为空，material 为空

    不允许 material 和 product 同时为空，也不允许同时有值。
    """

    material = models.ForeignKey(
        Material,
        verbose_name="物料",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    product = models.ForeignKey(
        Product,
        verbose_name="产品",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    warehouse = models.ForeignKey(
        Warehouse,
        verbose_name="仓库",
        on_delete=models.PROTECT,
    )

    batch_no = models.CharField("批次号", max_length=100)
    supplier = models.ForeignKey(
        Supplier,
        verbose_name="供应商",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    quantity = models.DecimalField("当前库存数量", max_digits=14, decimal_places=3, default=0)
    unit = models.CharField("单位", max_length=20, default="kg")

    unit_cost = models.DecimalField(
        "本批次成本单价",
        max_digits=12,
        decimal_places=4,
        default=0,
        help_text="这一批库存的实际成本单价。后续采购入库时会自动带入采购单价。",
    )

    production_date = models.DateField("生产日期", null=True, blank=True)
    expiry_date = models.DateField("有效期", null=True, blank=True)

    note = models.TextField("备注", blank=True)
    is_active = models.BooleanField("启用", default=True)

    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "库存批次"
        verbose_name_plural = "库存批次"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["material", "warehouse", "batch_no"],
                name="unique_material_batch_in_warehouse",
            ),
            models.UniqueConstraint(
                fields=["product", "warehouse", "batch_no"],
                name="unique_product_batch_in_warehouse",
            ),
        ]

    def clean(self):
        super().clean()

        if self.material is None and self.product is None:
            raise ValidationError("库存批次必须选择一个物料或一个产品。")

        if self.material is not None and self.product is not None:
            raise ValidationError("库存批次不能同时选择物料和产品。")

        if self.quantity < 0:
            raise ValidationError("当前库存数量不能为负数。")

        if self.unit_cost < 0:
            raise ValidationError("本批次成本单价不能为负数。")

    @property
    def total_cost(self):
        return self.quantity * self.unit_cost

    @property
    def item_code(self):
        if self.material:
            return self.material.code
        if self.product:
            return self.product.code
        return "-"

    @property
    def item_name(self):
        if self.material:
            return self.material.name
        if self.product:
            return self.product.name
        return "-"

    @property
    def item_type(self):
        if self.material:
            return "物料"
        if self.product:
            return "产品"
        return "-"

    def __str__(self):
        return f"{self.item_code} - {self.item_name} - {self.batch_no}"


class StockMovement(models.Model):
    """
    库存流水。

    注意：
    - 创建流水时不会自动改变库存。
    - 在 Django Admin 里选择流水，执行“应用库存流水”后，才会更新 StockBatch.quantity。
    - 这样做是为了避免误填数据后立刻污染库存。
    """

    MOVEMENT_TYPE_IN = "in"
    MOVEMENT_TYPE_OUT = "out"
    MOVEMENT_TYPE_ADJUST = "adjust"

    MOVEMENT_TYPE_CHOICES = [
        (MOVEMENT_TYPE_IN, "入库"),
        (MOVEMENT_TYPE_OUT, "出库"),
        (MOVEMENT_TYPE_ADJUST, "库存调整"),
    ]

    stock_batch = models.ForeignKey(
        StockBatch,
        verbose_name="库存批次",
        on_delete=models.PROTECT,
        related_name="movements",
    )

    movement_type = models.CharField(
        "流水类型",
        max_length=20,
        choices=MOVEMENT_TYPE_CHOICES,
    )

    quantity = models.DecimalField(
        "数量",
        max_digits=14,
        decimal_places=3,
        help_text="入库/出库填写正数；库存调整可以填写正数或负数。",
    )

    before_quantity = models.DecimalField(
        "变动前库存",
        max_digits=14,
        decimal_places=3,
        null=True,
        blank=True,
    )
    after_quantity = models.DecimalField(
        "变动后库存",
        max_digits=14,
        decimal_places=3,
        null=True,
        blank=True,
    )

    document_no = models.CharField("来源单号", max_length=100, blank=True)
    reason = models.CharField("原因", max_length=200, blank=True)
    note = models.TextField("备注", blank=True)

    is_applied = models.BooleanField("是否已应用", default=False)
    applied_at = models.DateTimeField("应用时间", null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="创建人",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "库存流水"
        verbose_name_plural = "库存流水"
        ordering = ["-created_at"]

    def clean(self):
        super().clean()

        if self.quantity == Decimal("0"):
            raise ValidationError("数量不能为 0。")

        if self.movement_type in [self.MOVEMENT_TYPE_IN, self.MOVEMENT_TYPE_OUT]:
            if self.quantity <= 0:
                raise ValidationError("入库和出库数量必须为正数。")

    def apply(self):
        """
        应用库存流水，真正修改库存批次数量。
        """

        if self.is_applied:
            raise ValidationError("这条库存流水已经应用过，不能重复应用。")

        self.full_clean()

        with transaction.atomic():
            batch = StockBatch.objects.select_for_update().get(pk=self.stock_batch_id)

            before_quantity = batch.quantity

            if self.movement_type == self.MOVEMENT_TYPE_IN:
                after_quantity = before_quantity + self.quantity

            elif self.movement_type == self.MOVEMENT_TYPE_OUT:
                after_quantity = before_quantity - self.quantity

            elif self.movement_type == self.MOVEMENT_TYPE_ADJUST:
                after_quantity = before_quantity + self.quantity

            else:
                raise ValidationError("未知的库存流水类型。")

            if after_quantity < 0:
                raise ValidationError(
                    f"库存不足。当前库存 {before_quantity}，本次变动 {self.quantity}。"
                )

            batch.quantity = after_quantity
            batch.save(update_fields=["quantity", "updated_at"])

            self.before_quantity = before_quantity
            self.after_quantity = after_quantity
            self.is_applied = True
            self.applied_at = timezone.now()
            self.save(
                update_fields=[
                    "before_quantity",
                    "after_quantity",
                    "is_applied",
                    "applied_at",
                    "updated_at",
                ]
            )

    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.stock_batch} - {self.quantity}"
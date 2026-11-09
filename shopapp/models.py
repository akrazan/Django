from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator

from django.db import models
from django.urls import reverse


class Product(models.Model):
    name = models.CharField("Наименование",
        max_length=100,
    )

    description = models.TextField("Описание товара",)

    price = models.DecimalField("Цена (руб.)",
        default=0,
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(1000000),
        ],
    )

    discount = models.SmallIntegerField("Скидка",
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
    )

    created_at = models.DateTimeField("Дата записи", auto_now_add=True,)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='products',
        null = False,
        blank = False,
    )

    archived = models.BooleanField("Архив", default=False,)

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

    def __str__(self):
        return f'Товар (№: {self.pk}, наименование: {self.name!r})'

    @property
    def description_short(self) -> str:
        if len(self.description) < 48:
            return self.description
        return self.description[:48] + '...'

    @property
    def description_rss(self) -> str:
        if len(self.description) < 200:
            return self.description
        return self.description[:200] + '...'

    # Валидация текстовых полей
    def clean(self):
        errors = {}

        if self.name:
            len_name = len(self.name.strip())
            if not (2 <= len_name <= 100):
                errors["name"] = "Наименование должно содержать от 2 до 100 символов."

        if not self.description or not self.description.strip():
            errors["description"] = "Описание товара обязательно для заполнения."

        if errors:
            raise ValidationError(errors)

    def get_absolute_url(self):
        return reverse('shopapp:product_detail', kwargs={'pk': self.pk})


class Order(models.Model):
    delivery_address = models.TextField(
        "Адрес доставки",
        max_length=200,
        blank=True,
        null=True,
    )
    promo_code = models.CharField(
        "Промокод",
        max_length=20,
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(
        "Дата заказа",
        auto_now_add=True,
    )
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name="Клиент",
    )
    products = models.ManyToManyField(
        Product,
        related_name="orders",
        verbose_name="Товары",
    )

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def __str__(self):
        return f'Заказ (№: {self.pk}, клиент: {self.user.username!r})'

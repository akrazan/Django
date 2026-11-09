import csv
import io

from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model

from .admin_mixins import ExpotrAsCSV
from .forms import CSVImportForm
from .models import Product, Order
from .views import export_orders_csv_view


@admin.action(description="Архивировать товары")
def mark_as_archived(modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet):
    queryset.update(archived=True)

@admin.action(description="Разархивировать товары")
def mark_as_unarchived(modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet):
    queryset.update(archived=False)


class OrderInline(admin.StackedInline):
    model = Product.orders.through

    verbose_name = "Заказ"
    verbose_name_plural = "Заказы с товаром"


@admin.register(Product)
class ProductAdmin(ExpotrAsCSV, admin.ModelAdmin):
    actions = [
        mark_as_archived,
        mark_as_unarchived,
        ExpotrAsCSV.export_to_csv,
    ]
    inlines = [
        OrderInline,
    ]
    fieldsets = (
        (None, {
            'fields': ('name', 'description')
        }),
        ("Опции цены", {
            'fields': ('price', 'discount'),
            'classes': ('collapse',)
        }),
        ("Дополнительные опции",{
            'fields': ('archived',),
            'classes': ('collapse',),
            'description': 'Архивный товар не отображается для новых заказов.'
        }
         )
    )
    list_display = ('pk', 'name', 'description_short', 'price', 'discount', 'created_at', 'archived')
    list_display_links = ('pk', 'name')
    ordering = ('name', 'pk')
    search_fields = ('name', 'description', 'price', 'discount')

    def description_short(self, obj):
        return obj.description_short
    description_short.short_description = "Краткое описание"

class ProductInline(admin.StackedInline):
    model = Order.products.through

    verbose_name = "Товар"
    verbose_name_plural = "Товары в заказе"


# ---------------- Загрузка заказов из файла ----------------
User = get_user_model()

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    change_list_template = "admin/shopapp/order_changelist.html"
    inlines = [
        ProductInline,
    ]
    list_display = ('pk', 'name_verbose', 'delivery_address', 'promo_code', 'created_at')
    list_display_links = ('pk', 'name_verbose')
    search_fields = ('user__first_name',  'user__last_name', 'user__username', 'delivery_address', 'promo_code')

    def get_queryset(self, request):
        return (
            Order.objects
            .select_related('user')
            .prefetch_related('products')
        )

    def name_verbose(self, obj) -> str:
        if not obj.user.first_name and not obj.user.last_name:
            return obj.user.username
        return obj.user.first_name + ' ' + obj.user.last_name
    name_verbose.short_description = "Клиент"

    def import_orders_csv_view(self, request: HttpRequest) -> HttpResponse:
        if request.method == "POST":  # метод POST - импортируем заказы
            form = CSVImportForm(request.POST, request.FILES)
            if form.is_valid():  # передан файл
                file = form.cleaned_data.get("csv_file")
                # file = request.FILES["file"]
                try:  # файл в формате "utf-8"
                    decoded_file = file.read().decode("utf-8")
                except UnicodeDecodeError:
                    messages.error(request, "Файл не в кодировке UTF-8.")
                    return render(
                        request,
                        "admin/shopapp/csv_form.html",
                        {"form": form, "title": "Импорт заказов", "opts": self.model._meta, "app_label": self.model._meta.app_label},
                    )

                # читаем файл
                io_string = io.StringIO(decoded_file)
                reader = csv.DictReader(io_string)

                errors = []
                success_count = 0

                # читаем данные построчно
                for row_num, row in enumerate(reader, start=2):
                    try:  # вытаскиваем данные из строки
                        username = row.get("username", "").strip()
                        delivery_address = row.get("delivery_address", "").strip() or None
                        promo_code = row.get("promo_code", "").strip() or None
                        product_ids_raw = row.get("product_ids", "").strip()

                        if not username:  # если username отсутствует - пропускаем заказ
                            errors.append(f"Строка {row_num}: отсутствует username")
                            continue

                        # Поиск пользователя
                        try:
                            user = User.objects.get(username=username)
                        except User.DoesNotExist:  # не нашли user - пропускаем заказ
                            errors.append(f"Строка {row_num}: пользователь username={username} не найден")
                            continue

                        # Парсинг списка товаров
                        product_ids = [pid.strip() for pid in product_ids_raw.split(",") if pid.strip()]
                        if not product_ids:  # список товаров пустой - пропускаем заказ
                            errors.append(f"Строка {row_num}: нет товаров (поле product_ids)")
                            continue

                        products = list(Product.objects.filter(id__in=product_ids))
                        found_ids = {str(p.id) for p in products}
                        missing_ids = set(product_ids) - found_ids

                        if missing_ids:  # Не найден хотя бы один товар - пропускаем заказ
                            errors.append(f"Строка {row_num}: не найдены товары с ID: {', '.join(missing_ids)}")
                            continue

                        # Всё нашли в БД - создаем заказ
                        order = Order.objects.create(
                            user=user,
                            delivery_address=delivery_address,
                            promo_code=promo_code,
                        )

                        # Привязываем товары (ManyToMany)
                        order.products.set(products)

                        success_count += 1

                    except Exception as e:  # если что-то пошло не так - фиксируем в список
                        errors.append(f"Строка {row_num}: ошибка — {e}")

                if errors:  # сообщаем об ошибках
                    for err in errors:
                        messages.error(request, err)
                else:  # загрузка прошла успешно
                    messages.success(request, f"Импорт завершён. Создано заказов: {success_count}")

                return redirect("..")  # Назад к списку заказов

        else:  # метод GET - выводим форму
            form = CSVImportForm()

        context = {
            "form": form,
            "title": "Импорт заказов",
            "opts": self.model._meta,
            "app_label": self.model._meta.app_label,
        }
        return render(request, "admin/shopapp/csv_form.html", context)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["export_csv_url"] = request.build_absolute_uri(
            f"{request.path}export-orders-csv/"
        )
        return super().changelist_view(request, extra_context=extra_context)

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [
            path("export-orders-csv/", export_orders_csv_view, name="export_orders_csv"),
            path(
                "import-orders-csv/",
                self.import_orders_csv_view,
                name="import_orders_csv",
            ),
        ]
        return new_urls + urls


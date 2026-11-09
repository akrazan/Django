import csv
import io
from datetime import datetime

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from rest_framework.viewsets import ModelViewSet
from django.contrib.syndication.views import Feed

from .models import Product, Order, User
from .serializers import ProductSerializer, OrderSerializer

YEAR = datetime.now().year


class ShopIndexView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        return render(request, "shopapp/index.html")


# ------- Классы-представления на базе ModelViewSet -------

class ProductViewSet(ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    # Поиск
    search_fields = ['name', 'description', 'archived']

    # Сортировка
    ordering_fields = ['created_by', 'name', 'price']


class OrderViewSet(ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    # Фильтрация
    filterset_fields = ['delivery_address', 'promo_code', 'user']

    # Сортировка
    ordering_fields = ['user', 'promo_code']


# ------- Классы-представления для товара -------

class ProductsListView(ListView):
    queryset = Product.objects.filter(archived=False)


class ProductsDetailView(DetailView):
    model = Product


class ProductsCreateView(PermissionRequiredMixin, CreateView):
    model = Product
    fields = ["name", "description", "price", "discount"]
    success_url = reverse_lazy("shopapp:product_list")
    permission_required = "shopapp.add_product"

    def form_valid(self, form):
        product = form.save(commit=False)
        product.created_by = self.request.user
        product.save()
        return super().form_valid(form)


class ProductsUpdateView(
    PermissionRequiredMixin,  # авторизирован ли пользователь и есть ли у него право изменять товары
    UserPassesTestMixin,  #  есть ли у него право на изменение обрабатываемого товара
    UpdateView  # тогда используем базовый класс
):

    model = Product
    fields = ["name", "description", "price", "discount"]
    template_name_suffix = "_update_form"
    permission_required = "shopapp.change_product"

    def test_func(self):
        obj = self.get_object()
        return self.request.user.is_superuser or obj.created_by == self.request.user

    def get_success_url(self):
        return reverse("shopapp:product_detail", kwargs={"pk": self.object.pk})


class ProductsArchiveView(PermissionRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Product
    template_name_suffix = "_archive"
    success_url = reverse_lazy("shopapp:product_list")
    permission_required = "shopapp.delete_product"

    def test_func(self):
        obj = self.get_object()
        return self.request.user.is_superuser or obj.created_by == self.request.user

    def form_valid(self, form) -> HttpResponseRedirect:
        self.object.archived = True
        self.object.save(update_fields=["archived"])
        return HttpResponseRedirect(self.get_success_url())


# ------- Классы-представления для заказа -------

class OrdersListView(ListView):
    queryset = (Order.objects
                .select_related("user")
                .prefetch_related("products"))


class OrdersDetailView(DetailView):
    queryset = (Order.objects
                .select_related("user")
                .prefetch_related("products"))


class OrderCreateView(CreateView):
    model = Order
    fields = ["user", "delivery_address", "promo_code", "products"]
    success_url = reverse_lazy("shopapp:order_list")


class OrderUpdateView(UpdateView):
    model = Order
    fields = ["user", "delivery_address", "promo_code", "products"]
    template_name_suffix = "_update_form"

    def get_success_url(self):
        return reverse("shopapp:order_detail", kwargs={"pk": self.object.pk})


class OrderDeleteView(DeleteView):
    model = Order
    template_name_suffix = "_delete"
    success_url = reverse_lazy("shopapp:order_list")


class UserOrdersExportView(LoginRequiredMixin, View):
    """Экспорт заказов пользователя в JSON с кешированием."""
    cache_timeout = 300  # кеш на 5 минут

    def get(self, request: HttpRequest, user_id: int) -> JsonResponse:
        # ключ с учётом идентификатора пользователя
        cache_key = f"user_orders_export_{user_id}"

        # Пытаемся получить данные из кеша
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            print(f"Данные получены из кеша: {cache_key}")
            return JsonResponse(cached_data, safe=False)

        # Кеш отсутствует - работаем с БД.
        # Пытаемся получить пользователя, если пользователь не найден — 404
        user = get_object_or_404(User, pk=user_id)

        # Загружаем заказы пользователя, сортировка по ключу
        orders_qs = Order.objects.filter(user=user).order_by("pk").prefetch_related('products')

        # Сериализуем данные
        serializer = OrderSerializer(orders_qs, many=True)
        data = serializer.data

        # Сохраняем в кеш
        cache.set(cache_key, data, self.cache_timeout)

        print(f"Данные получены из БД: {user.username}")

        return JsonResponse(data, safe=False)


class UserOrdersListView(LoginRequiredMixin, ListView):
    template_name = "shopapp/user_orders.html"
    context_object_name = "orders"

    def get_queryset(self):
        # 404, если пользователя с таким ID нет
        self.owner = get_object_or_404(User, pk=self.kwargs["user_id"])
        return Order.objects.filter(user=self.owner)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["owner"] = self.owner  # не называем переменную "user" — она занята
        return context


@user_passes_test(lambda u: u.is_staff)
def export_orders_json(request) -> JsonResponse:
    orders = []
    for order in Order.objects.all():
        orders.append({
            "id": order.pk,
            "address": order.delivery_address,
            "promo_code": order.promo_code,
            "user_id": order.user.id,
            "product_ids": list(order.products.values_list("pk", flat=True)),
        })
    return JsonResponse({"orders": orders})


@staff_member_required
def export_orders_csv_view(request: HttpRequest) -> HttpResponse:
    # Получаем все заказы
    orders = Order.objects.all().select_related('user').prefetch_related('products')

    # Создаём буфер в памяти
    output = io.StringIO()
    writer = csv.writer(output)

    # Заголовки — те, что ожидает импорт
    header = [
        "username",
        "delivery_address",
        "promo_code",
        "product_ids"
    ]
    writer.writerow(header)

    for order in orders:
        # username пользователя
        username = order.user.username if order.user else ""

        # адрес доставки и промокод (если None — пишем пустую строку)
        delivery_address = order.delivery_address or ""
        promo_code = order.promo_code or ""

        # Собираем ID товаров через запятую
        product_ids = ",".join(str(p.id) for p in order.products.all())

        writer.writerow([
            username,
            delivery_address,
            promo_code,
            product_ids
        ])

    # Формируем HTTP-ответ с CSV
    response = HttpResponse(output.getvalue(), content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="orders_export.csv"'
    return response



# ------- Класс RSS -------

class LatestProductsFeed(Feed):
    title = "Новые товары магазина"
    link = "/products/"
    description = "Самые свежие товары, добавленные в магазин."

    def items(self):
        # Используем created_at, сортируем по убыванию,
        # берём 10 последних неархивных товаров
        return Product.objects.filter(archived=False).order_by('-created_at')[:10]

    def item_title(self, item: Product) -> str:
        return item.name

    def item_description(self, item: Product) -> str:
        # В описание берём description_rss (200 символов)
        return item.description_rss

    def item_link(self, item: Product) -> str:
        # Ссылка через get_absolute_url
        return item.get_absolute_url()
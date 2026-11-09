from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse
from .models import Order, Product


User = get_user_model()


class OrderDetailViewTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Перед тестами происходит создание пользователя
        cls.user = User.objects.create_user(
            username='test_user',
            password='test_password'
        )

        # Получаем ContentType для заказов
        content_type = ContentType.objects.get_for_model(Order)

        # Получаем разрешение view_order для заказов
        perm = Permission.objects.get(
            codename='view_order',
            content_type=content_type
        )

        # Пользователю выдаются необходимые права для просмотра заказа
        cls.user.user_permissions.add(perm)
        cls.user.refresh_from_db()

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'user') and cls.user:
            # После тестов выполняется удаление пользователя
            cls.user.delete()
        super().tearDownClass()

    def setUp(self):
        # Перед тестом выполняется вход пользователя
        self.client.force_login(self.user)

        # Перед тестом выполняется создание заказа
        self.order = Order.objects.create(
            user=self.user,
            delivery_address='г.Тестовый, ул. Тестовая, д. 10',
            promo_code='PROMO2026'
        )

    def tearDown(self):
        if hasattr(self, 'order') and self.order:
            # После теста заказ удаляется
            self.order.delete()

    def test_order_details(self):
        url = reverse('shopapp:order_detail', kwargs={'pk': self.order.pk})
        response = self.client.get(url)

        # Проверка: статус кода-ответа — 200
        self.assertEqual(response.status_code, 200)

        # Проверка: в теле ответа есть адрес заказа
        self.assertContains(response, self.order.delivery_address)

        # Проверка: в теле ответа есть промокод
        self.assertContains(response, self.order.promo_code)

        # Проверка: в контексте ответа тот же заказ, который был создан перед тестом
        context_obj = response.context.get('object') or response.context.get('order')
        self.assertIsNotNone(context_obj)  # в ответе есть хоть какой-то
        self.assertEqual(context_obj.pk, self.order.pk)  # в ответе именно тестовый


class OrdersExportTestCase(TestCase):
    # загружаются фикстуры
    fixtures = [
        "fixtures/groups.json",
        "fixtures/users.json",
        "fixtures/products.json",
        "fixtures/orders.json",
    ]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Перед тестами: создание пользователя с правами is_staff
        cls.staff_user = User.objects.create_user(
            username="staff_test",
            password="password",
            is_staff=True,
        )

    @classmethod
    def tearDownClass(cls):
        # После всех тестов: удаление пользователя
        if hasattr(cls, "staff_user") and cls.staff_user:
            cls.staff_user.delete()
        super().tearDownClass()

    def setUp(self):
        # Перед каждым тестом: вход пользователя
        self.client.login(username="staff_test", password="password")

    def test_export_orders_returns_200_and_correct_data(self):
        url = reverse("shopapp:export_orders")
        response = self.client.get(url)

        # Проверка статуса кода ответа — 200
        self.assertEqual(response.status_code, 200)

        # получаем список заказов из response
        data = response.json()
        self.assertIn("orders", data)
        http_orders = data["orders"]
        http_orders_sorted = sorted(http_orders, key=lambda x: x["id"])

        # получаем список заказов из db
        db_orders = []
        for order in Order.objects.select_related("user").prefetch_related("products").all():

            product_ids = list(order.products.values_list("pk", flat=True))

            db_orders.append({
                "id": order.pk,
                "address": order.delivery_address,
                "promo_code": order.promo_code,
                "user_id": order.user.id,
                "product_ids": product_ids,
            })

        db_orders_sorted = sorted(db_orders, key=lambda x: x["id"])

        # Тест идентичности списков
        self.assertEqual(http_orders_sorted, db_orders_sorted)

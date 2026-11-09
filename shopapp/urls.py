from django.contrib.sitemaps.views import sitemap
from django.urls import path, include

from rest_framework.routers import DefaultRouter

from . import views   # <-- относительный импорт
from .sitemap import ShopSitemap

app_name = "shopapp"

router = DefaultRouter()
router.register("products", views.ProductViewSet)
router.register("orders", views.OrderViewSet)


sitemaps = {
    'shop': ShopSitemap,
}

urlpatterns = [
    path('', views.ShopIndexView.as_view(), name='index'),
    path('api/', include(router.urls)),
    path("products/", views.ProductsListView.as_view(), name="product_list"),
    path("products/<int:pk>/", views.ProductsDetailView.as_view(), name="product_detail"),
    path("products/create/", views.ProductsCreateView.as_view(), name="product_create"),
    path("products/<int:pk>/update", views.ProductsUpdateView.as_view(), name="product_update"),
    path("products/<int:pk>/archive", views.ProductsArchiveView.as_view(), name="product_archive"),
    path("orders/", views.OrdersListView.as_view(), name="order_list"),
    path("orders/<int:pk>/", views.OrdersDetailView.as_view(), name="order_detail"),
    path("orders/create/", views.OrderCreateView.as_view(), name="order_create"),
    path("orders/<int:pk>/update", views.OrderUpdateView.as_view(), name="order_update"),
    path("orders/<int:pk>/delete", views.OrderDeleteView.as_view(), name="order_delete"),
    path("users/<int:user_id>/orders/export/", views.UserOrdersExportView.as_view(), name="user_orders_export"),
    path("users/<int:user_id>/orders/", views.UserOrdersListView.as_view(), name="user_orders"),
    path("orders/export/", views.export_orders_json, name="export_orders"),

    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='shopapp_sitemap'),

    path('products/latest/feed/', views.LatestProductsFeed(), name='latest_products_feed'),

]

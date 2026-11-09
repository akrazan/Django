from django.contrib.sitemaps import Sitemap

from .models import Product


class ShopSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Product.objects.filter(archived=False).order_by('name')

    def lastmod(self, obj: Product):
        return obj.created_at

    def location(self, obj: Product):
        return obj.get_absolute_url()
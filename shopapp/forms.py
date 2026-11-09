from django import forms

from shopapp.models import Product, Order


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "description", "price", "discount"]

    # --- Валидаторы полей ---
    def clean_name(self):
        name = self.cleaned_data.get("name")
        if name:
            len_name = len(name.strip())
            if not (2 <= len_name <= 100):
                raise forms.ValidationError("Наименование должно содержать от 2 до 100 символов.")
        return name

    def clean_description(self):
        description = self.cleaned_data.get("description")
        if not description or not description.strip():
            raise forms.ValidationError("Описание товара обязательно для заполнения.")
        return description

    def clean_discount(self):
        discount = self.cleaned_data.get("discount")
        if discount is not None and not (0 <= discount <= 100):
            raise forms.ValidationError("Скидка должна быть в диапазоне от 0 до 100.")
        return discount

    def clean_price(self):
        price = self.cleaned_data.get("price")
        if price is not None and not (0 <= price <= 1000000):
            raise forms.ValidationError("Цена должна быть в диапазоне от 0 до 1000000.")
        return price


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["user", "delivery_address", "promo_code", "products"]

    # валидатор адреса доставки
    def clean_delivery_address(self):
        delivery_address = self.cleaned_data.get("delivery_address")
        if not delivery_address or not delivery_address.strip():
            raise forms.ValidationError("Адрес доставки обязателен для заполнения.")
        return delivery_address


class CSVImportForm(forms.Form):
    csv_file = forms.FileField(label="Файл для импорта (CSV)")
from django import forms
from django.core.exceptions import ValidationError
import re
from .models import Order

class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'email', 'address', 'city', 'postcode', 'phone_number']
        labels = {
            'first_name': 'نام',
            'last_name': 'نام خانوادگی',
            'email': 'ایمیل',
            'address': 'آدرس',
            'city': 'شهر',
            'postcode': 'کد پستی',
            'phone_number': 'شماره موبایل',
        }

    def clean_postcode(self):
        postcode = self.cleaned_data.get('postcode')
        if not re.match(r'^\d{10}$', postcode):
            raise ValidationError("کد پستی باید دقیقاً ۱۰ رقم باشد.")
        return postcode

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if not re.match(r'^09\d{9}$', phone):
            raise ValidationError("شماره موبایل باید ۱۱ رقم باشد و با 09 شروع شود.")
        return phone

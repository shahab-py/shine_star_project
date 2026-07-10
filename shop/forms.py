from django import forms
from django.core.exceptions import ValidationError
import re

class OrderCreateForm(forms.Form):
    first_name = forms.CharField(max_length=50, label="نام")
    last_name = forms.CharField(max_length=50, label="نام خانوادگی")
    email = forms.EmailField(label="ایمیل")
    address = forms.CharField(widget=forms.Textarea, label="آدرس")
    city = forms.CharField(max_length=50, label="شهر")
    postcode = forms.CharField(max_length=10, label="کد پستی")
    phone_number = forms.CharField(max_length=11, label="شماره موبایل")

    # اعتبارسنجی کد پستی (۱۰ رقم)
    def clean_postcode(self):
        postcode = self.cleaned_data.get('postcode')
        if not re.match(r'^\d{10}$', postcode):
            raise ValidationError("کد پستی باید دقیقاً ۱۰ رقم باشد.")
        return postcode

    # اعتبارسنجی شماره موبایل (۱۱ رقم، شروع با 09)
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if not re.match(r'^09\d{9}$', phone):
            raise ValidationError("شماره موبایل باید ۱۱ رقم باشد و با 09 شروع شود.")
        return phone

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User

class UserRegistrationForm(UserCreationForm):
    username = forms.CharField(label="نام کاربری", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثلاً: star_user'}))
    email = forms.EmailField(label="ایمیل", widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'example@mail.com'}))
    first_name = forms.CharField(label="نام", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام خود را وارد کنید'}))
    last_name = forms.CharField(label="نام خانوادگی", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام خانوادگی را وارد کنید'}))
    phone_number = forms.CharField(label="شماره موبایل", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '۰۹۱۲XXXXXXX'}))
    bio = forms.CharField(label="درباره من", widget=forms.Textarea(attrs={
        'class': 'form-control', 
        'placeholder': 'کمی درباره خودتان بنویسید...',
        'rows': 3
    }), required=False)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone_number', 'bio')
    password1 = forms.CharField(label="رمز عبور", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label="تکرار رمز عبور", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(label="نام", widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label="نام خانوادگی", widget=forms.TextInput(attrs={'class': 'form-control'}))
    bio = forms.CharField(label="درباره من", widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}), required=False)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'bio')

class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'نام کاربری یا ایمیل'
        }),
        label='نام کاربری'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'رمز عبور',
            'id': 'id_password'
        }),
        label='رمز عبور'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_messages = {
            'inactive': 'این حساب کاربری غیرفعال است.',
            'bad_credentials': 'نام کاربری یا رمز عبور اشتباه است.',
            'none': 'لطفاً نام کاربری و رمز عبور را وارد کنید.',
        }
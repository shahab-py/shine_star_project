import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from accounts.factories import UserFactory
from accounts.models import User

User = get_user_model()

@pytest.mark.django_db
class TestUserModel:
    """تست‌های مربوط به مدل User و UserManager"""

    def test_create_user_with_email_raises_error(self):
        """باید اگر ایمیل داده نشود، خطا دهد"""
        with pytest.raises(ValueError, match='Users must have an email address'):
            User.objects.create_user(username="testuser", email=None, password="password")

    def test_create_superuser(self):
        """تست ساخت سوپر یوزر"""
        admin = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpassword"
        )
        assert admin.is_superuser is True
        assert admin.is_staff is True
        assert admin.email == "admin@example.com"

    def test_user_str_representation(self):
        """تست رشته نمایش مدل"""
        user = UserFactory(username="kosar", email="kosar@test.com")
        assert str(user) == "kosar (kosar@test.com)"


@pytest.mark.django_db
class TestAccountViews:
    """تست‌های مربوط به ویوها و جریان‌های کاربر"""


    @pytest.fixture
    def user(self):
        user = UserFactory()
        user.set_password('securepassword123')
        user.save()
        return user

    def test_register_view_get(self, client):
        """تست نمایش فرم ثبت‌نام"""
        url = reverse('accounts:register')
        response = client.get(url)
        assert response.status_code == 200
        assert 'form' in response.context

    def test_register_view_post_success(self, client):
        """تست ثبت‌نام موفقیت‌آمیز"""
        url = reverse('accounts:register')
        data = {
            'username': 'newuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'phone_number': '09120000000',
            'bio': 'Test bio',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }
        response = client.post(url, data)
        
        assert User.objects.filter(username='newuser').exists()
        assert response.status_code == 302  # Redirect به shop:home

    def test_profile_view_requires_login(self, client):
        """تست اینکه پروفایل فقط برای کاربران لاگین شده قابل دسترسی است"""
        url = reverse('accounts:profile')
        response = client.get(url)
        assert response.status_code == 302

    @pytest.mark.django_db
    def test_profile_view_authenticated(self, client):
        user = UserFactory()
        client.force_login(user)
        response = client.get(reverse('accounts:profile'))
        assert response.status_code == 200


    def test_logout_view(self, client, user):
        """تست خروج از سیستم"""
        client.login(username=user.username, password=user.password)
        url = reverse('accounts:logout')
        response = client.post(url)
        
        assert response.status_code == 302
        assert '_auth_user_id' not in client.session

    @pytest.mark.django_db
    def test_profile_edit_view_post(self, client):
        user = UserFactory()

        client.force_login(user)

        data = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'phone_number': user.phone_number,
            'bio': 'New bio content',
            'birth_date': '1990-01-01',
        }

        response = client.post(
            reverse('accounts:profile_edit'),
            data=data,
        )

        assert response.status_code in [200, 302]

        user.refresh_from_db()

        assert user.bio == 'New bio content'


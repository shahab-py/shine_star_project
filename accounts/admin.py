from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User

    list_display = (
        'id',
        'username',
        'email',
        'phone_number',
        'is_verified',
        'is_premium',
        'is_staff',
        'is_active',
    )
    list_filter = (
        'is_verified',
        'is_premium',
        'is_staff',
        'is_active',
        'groups',
    )
    search_fields = ('username', 'email', 'phone_number')
    ordering = ('id',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {
            'fields': (
                'first_name',
                'last_name',
                'email',
                'phone_number',
                'bio',
                'birth_date',
                'profile_picture',
            )
        }),
        ('Status', {
            'fields': (
                'is_verified',
                'is_premium',
            )
        }),
        ('Permissions', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            )
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username',
                'email',
                'phone_number',
                'password1',
                'password2',
                'is_verified',
                'is_premium',
                'is_staff',
                'is_superuser',
            ),
        }),
    )

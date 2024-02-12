"""Users admin config."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Админ-панель модели пользователя"""

    list_display = (
        'username',
        'email',
        'is_active',
        'is_staff',
        'date_joined',
        'words_in_vocabulary',
    )
    list_filter = (
        'username',
        'email',
    )
    search_fields = (
        'username',
        'email',
    )
    ordering = ('-date_joined',)
    prepopulated_fields = {'slug': ('username',)}

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (
            'Personal info',
            {
                'fields': (
                    'email',
                    'slug',
                    'gender',
                )
            },
        ),
        (
            'Permissions',
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'groups',
                    'user_permissions',
                )
            },
        ),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'username',
                    'email',
                    'password1',
                    'password2',
                    'slug',
                ),
            },
        ),
    )

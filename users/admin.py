"""Users admin config."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    User,
    UserDefaultWordsView,
    UserLearningLanguage,
    UserNativeLanguage,
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Админ-панель модели пользователя"""

    list_display = (
        'username',
        'email',
        'is_active',
        'is_staff',
        'date_joined',
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


admin.site.register(UserDefaultWordsView)
admin.site.register(UserLearningLanguage)
admin.site.register(UserNativeLanguage)

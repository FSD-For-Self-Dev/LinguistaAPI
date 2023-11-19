''' Users admin config '''

from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    '''Админ-панель модели пользователя'''

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

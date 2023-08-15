''' Users admin config '''

from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    '''Админ-панель модели пользователя'''

    list_display = ('username', 'email')
    list_filter = ('username', 'email')

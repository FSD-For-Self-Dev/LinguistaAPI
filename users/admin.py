"""Административные настройки приложения users."""

from django.contrib import admin

from .models import User


@admin.site.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email')
    list_filter = ('username', 'email')

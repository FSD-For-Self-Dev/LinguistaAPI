"""Languages admin config."""

from django.contrib import admin

from .models import Language, LanguageImage


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    pass


@admin.register(LanguageImage)
class LanguageImageAdmin(admin.ModelAdmin):
    pass

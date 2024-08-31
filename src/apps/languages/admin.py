"""Languages app admin panel."""

from django.contrib import admin

from modeltranslation.admin import TabbedTranslationAdmin

from .models import Language, LanguageImage


@admin.register(Language)
class LanguageAdmin(TabbedTranslationAdmin):
    list_display = (
        'name',
        'name_local',
        'isocode',
        'sorting',
        'learning_available',
        'words_count',
    )
    search_fields = (
        'name',
        'name_local',
        'isocode',
    )
    ordering = ('-sorting', 'name')


@admin.register(LanguageImage)
class LanguageImageAdmin(admin.ModelAdmin):
    pass

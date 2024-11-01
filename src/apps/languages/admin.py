"""Languages app admin panel."""

from django.contrib import admin

from modeltranslation.admin import TabbedTranslationAdmin

from .models import (
    Language,
    LanguageCoverImage,
    UserNativeLanguage,
    UserLearningLanguage,
)


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


@admin.register(LanguageCoverImage)
class LanguageCoverImageAdmin(admin.ModelAdmin):
    list_display = (
        'language',
        'image',
        'image_size',
    )
    search_fields = ('language__name',)
    ordering = ('-language__sorting', 'language__name')


@admin.register(UserLearningLanguage)
class UserLearningLanguageAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('user', 'language')}
    pass


@admin.register(UserNativeLanguage)
class UserNativeLanguageAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('user', 'language')}
    pass

"""Конфигурация админ-панели приложения vocabulary."""

from django.contrib import admin

from .models import (
    Antonym, Collection, Definition, FavoriteCollection, FavoriteWord, Form,
    ImageAssociation, Note, Similar, Synonym, Tag, Translation, Type,
    UsageExample, Word, WordDefinitions, WordTranslations, WordUsageExamples,
    WordsInCollections
)


class WordTranslationInline(admin.TabularInline):
    model = WordTranslations
    min_num = 1


class SynonymInline(admin.TabularInline):
    model = Synonym
    fk_name = 'to_word'


class AntonymInline(admin.TabularInline):
    model = Antonym
    fk_name = 'to_word'


class FormInline(admin.TabularInline):
    model = Form
    fk_name = 'to_word'


class SimilarInline(admin.TabularInline):
    model = Similar
    fk_name = 'to_word'


class WordUsageExamplesInline(admin.TabularInline):
    model = WordUsageExamples


class WordDefinitionsInline(admin.TabularInline):
    model = WordDefinitions


class WordAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('text', 'author')}
    list_display = ('pk', 'text', 'author')
    search_fields = ('text', 'author')
    list_filter = ('author',)
    inlines = (
        WordTranslationInline, WordUsageExamplesInline,
        WordDefinitionsInline,
        SynonymInline,
        AntonymInline,
        FormInline,
        SimilarInline
    )


admin.site.register(Word, WordAdmin)
admin.site.register(Translation)
admin.site.register(WordTranslations)
admin.site.register(UsageExample)
admin.site.register(WordUsageExamples)
admin.site.register(Definition)
admin.site.register(WordDefinitions)
admin.site.register(Tag)
admin.site.register(Type)
admin.site.register(Collection)
admin.site.register(WordsInCollections)
admin.site.register(Synonym)
admin.site.register(Antonym)
admin.site.register(Form)
admin.site.register(Similar)
admin.site.register(Note)
admin.site.register(ImageAssociation)
admin.site.register(FavoriteWord)
admin.site.register(FavoriteCollection)

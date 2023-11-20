"""Конфигурация админ-панели приложения vocabulary."""

from django.contrib import admin

from modeltranslation.admin import TranslationAdmin

from .models import (
    Antonym, Collection, Definition, FavoriteCollection, FavoriteWord, Form,
    ImageAssociation, Note, Similar, Synonym, Tag, WordTranslation, Type,
    UsageExample, Word, WordDefinitions, WordsInCollections, WordTranslations,
    WordUsageExamples, FormsGroup, WordsFormGroups
)


class WordTranslationInline(admin.TabularInline):
    model = WordTranslations


class WordWordsFormGroupsInline(admin.TabularInline):
    model = WordsFormGroups


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


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('text', 'author')}
    list_display = ('pk', 'text', 'author')
    list_display_links = ('text',)
    search_fields = ('text', 'author__username')
    list_filter = ('author',)
    inlines = (
        WordWordsFormGroupsInline,
        WordTranslationInline, WordUsageExamplesInline,
        WordDefinitionsInline,
        SynonymInline,
        AntonymInline,
        FormInline,
        SimilarInline
    )


@admin.register(Type)
class TypeAdmin(TranslationAdmin):
    list_display = ('name', 'sorting') 
    list_display_links = ('name',)


class WordInLine(admin.TabularInline):
    model = WordsInCollections


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title', 'author')}
    list_display = ('id', 'title', 'author', 'words_count')
    list_display_links = ('title',)
    inlines = (
        WordInLine,
    )


@admin.register(FormsGroup)
class FormsGroupAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name', 'author')}
    list_display = ('id', 'name', 'author')
    list_display_links = ('name',)


admin.site.register(WordTranslation)
admin.site.register(WordTranslations)
admin.site.register(UsageExample)
admin.site.register(WordUsageExamples)
admin.site.register(Definition)
admin.site.register(WordDefinitions)
admin.site.register(Tag)
admin.site.register(WordsInCollections)
admin.site.register(Synonym)
admin.site.register(Antonym)
admin.site.register(Form)
admin.site.register(Similar)
admin.site.register(Note)
admin.site.register(ImageAssociation)
admin.site.register(FavoriteWord)
admin.site.register(FavoriteCollection)
admin.site.register(WordsFormGroups)

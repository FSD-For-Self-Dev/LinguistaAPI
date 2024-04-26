"""Конфигурация админ-панели приложения vocabulary."""

from django.contrib import admin

from modeltranslation.admin import TranslationAdmin

from .models import (
    Antonym,
    Collection,
    Definition,
    FavoriteCollection,
    FavoriteWord,
    Form,
    FormsGroup,
    ImageAssociation,
    Note,
    Similar,
    Synonym,
    Tag,
    Type,
    UsageExample,
    Word,
    WordDefinitions,
    WordsFormGroups,
    WordsInCollections,
    WordTranslation,
    WordTranslations,
    WordUsageExamples,
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
        WordTranslationInline,
        WordUsageExamplesInline,
        WordDefinitionsInline,
        SynonymInline,
        AntonymInline,
        FormInline,
        SimilarInline,
    )


@admin.register(Type)
class TypeAdmin(TranslationAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'words_count')
    list_display_links = ('name',)


class CollectionWordInLine(admin.TabularInline):
    model = WordsInCollections


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title', 'author')}
    list_display = ('title', 'author', 'words_count')
    list_display_links = ('title',)
    inlines = (CollectionWordInLine,)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'words_count')
    list_display_links = ('name',)


@admin.register(FormsGroup)
class FormsGroupAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name', 'author')}
    list_display = ('id', 'name', 'author', 'words_count')
    list_display_links = ('name',)


@admin.register(WordTranslation)
class WordTranslationAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('text', 'author')}
    list_display = ('id', 'text', 'language', 'words_count')
    list_display_links = ('text',)


@admin.register(UsageExample)
class UsageExampleAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('text', 'author')}
    list_display = ('id', 'text', 'translation', 'words_count')
    list_display_links = ('text',)


@admin.register(Definition)
class DefinitionAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('text', 'author')}
    list_display = ('id', 'text', 'translation', 'words_count')
    list_display_links = ('text',)


@admin.register(Synonym)
class SynonymAdmin(admin.ModelAdmin):
    list_display = ('id', 'from_word', 'to_word', 'note')
    list_display_links = ('from_word',)


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'text', 'word', 'created')
    list_display_links = ('text', 'word')


admin.site.register(WordTranslations)
admin.site.register(WordUsageExamples)
admin.site.register(WordDefinitions)
admin.site.register(WordsInCollections)
admin.site.register(Antonym)
admin.site.register(Form)
admin.site.register(Similar)
admin.site.register(ImageAssociation)
admin.site.register(FavoriteWord)
admin.site.register(FavoriteCollection)

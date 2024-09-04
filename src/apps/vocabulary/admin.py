"""Vocabulary app admin panel."""

from django.contrib import admin

from modeltranslation.admin import TabbedTranslationAdmin

from .models import (
    Antonym,
    Collection,
    Definition,
    FavoriteCollection,
    FavoriteWord,
    Form,
    FormGroup,
    ImageAssociation,
    Note,
    Similar,
    Synonym,
    WordTag,
    WordType,
    UsageExample,
    Word,
    WordDefinitions,
    WordsFormGroups,
    WordsInCollections,
    WordTranslation,
    WordTranslations,
    WordUsageExamples,
    QuoteAssociation,
    WordImageAssociations,
    WordQuoteAssociations,
    DefaultWordCards,
)


class WordTranslationInline(admin.TabularInline):
    model = WordTranslations


class WordFormGroupsInline(admin.TabularInline):
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


class NoteInline(admin.TabularInline):
    prepopulated_fields = {'slug': ('text',)}
    model = Note


class WordImageAssociationsInline(admin.TabularInline):
    model = WordImageAssociations


class WordQuoteAssociationsInline(admin.TabularInline):
    model = WordQuoteAssociations


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('text', 'author')}
    list_display = ('slug', 'text', 'author')
    list_display_links = ('slug',)
    search_fields = ('text', 'author__username')
    list_filter = ('author',)
    inlines = (
        WordFormGroupsInline,
        WordTranslationInline,
        WordUsageExamplesInline,
        WordDefinitionsInline,
        SynonymInline,
        AntonymInline,
        FormInline,
        SimilarInline,
        NoteInline,
        WordImageAssociationsInline,
        WordQuoteAssociationsInline,
    )


@admin.register(WordType)
class WordTypeAdmin(TabbedTranslationAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'slug', 'words_count')
    list_display_links = ('name',)


class CollectionWordInLine(admin.TabularInline):
    model = WordsInCollections


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title', 'author')}
    list_display = ('slug', 'title', 'author', 'words_count')
    list_display_links = ('slug',)
    inlines = (CollectionWordInLine,)


@admin.register(WordTag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'words_count')
    list_display_links = ('name',)


@admin.register(FormGroup)
class FormGroupAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name', 'author')}
    list_display = ('slug', 'name', 'author', 'words_count')
    list_display_links = ('slug',)


@admin.register(WordTranslation)
class WordTranslationAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('text', 'author')}
    list_display = ('slug', 'text', 'language', 'words_count')
    list_display_links = ('slug',)


@admin.register(UsageExample)
class UsageExampleAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('text', 'author')}
    list_display = ('slug', 'text', 'translation', 'words_count')
    list_display_links = ('slug',)


@admin.register(Definition)
class DefinitionAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('text', 'author')}
    list_display = ('slug', 'text', 'translation', 'words_count')
    list_display_links = ('slug',)


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('slug', 'text', 'word', 'created')
    list_display_links = ('slug',)


@admin.register(ImageAssociation)
class ImageAssociationAdmin(admin.ModelAdmin):
    pass


@admin.register(QuoteAssociation)
class QuoteAssociationAdmin(admin.ModelAdmin):
    pass


@admin.register(Synonym)
class SynonymAdmin(admin.ModelAdmin):
    list_display = ('from_word', 'to_word', 'note')
    list_display_links = ('from_word',)


@admin.register(Antonym)
class AntonymAdmin(admin.ModelAdmin):
    list_display = ('from_word', 'to_word', 'note')
    list_display_links = ('from_word',)


@admin.register(Form)
class FormAdmin(admin.ModelAdmin):
    list_display = ('from_word', 'to_word')
    list_display_links = ('from_word',)


@admin.register(Similar)
class SimilarAdmin(admin.ModelAdmin):
    list_display = ('from_word', 'to_word')
    list_display_links = ('from_word',)


@admin.register(FavoriteWord)
class FavoriteWordAdmin(admin.ModelAdmin):
    pass


@admin.register(FavoriteCollection)
class FavoriteCollectionAdmin(admin.ModelAdmin):
    pass


@admin.register(WordTranslations)
class WordTranslationsAdmin(admin.ModelAdmin):
    pass


@admin.register(WordUsageExamples)
class WordUsageExamplesAdmin(admin.ModelAdmin):
    pass


@admin.register(WordDefinitions)
class WordDefinitionsAdmin(admin.ModelAdmin):
    pass


@admin.register(WordsInCollections)
class WordsInCollectionsAdmin(admin.ModelAdmin):
    pass


@admin.register(WordImageAssociations)
class WordImageAssociationsAdmin(admin.ModelAdmin):
    pass


@admin.register(WordQuoteAssociations)
class WordQuoteAssociationsAdmin(admin.ModelAdmin):
    pass


@admin.register(WordsFormGroups)
class WordsFormGroupsAdmin(admin.ModelAdmin):
    pass


@admin.register(DefaultWordCards)
class DefaultWordCardsAdmin(admin.ModelAdmin):
    pass

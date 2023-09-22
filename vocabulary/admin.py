''' Vocabulary admin config '''

from django.contrib import admin

from .models import (
    Antonym, Collection, Definition, FavoriteCollection, FavoriteWord, Form,
    Note, Similar, Synonym, Tag, Translation, Type, UsageExample, Word,
    WordDefinitions, WordTranslations, WordUsageExamples, WordsInCollections,
    ImageAssociation
)


class WordTranslationInline(admin.TabularInline):
    model = WordTranslations
    min_num = 1


class WordAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('text', 'author')}
    list_display = ('pk', 'text', 'author')
    search_fields = ('text', 'author')
    list_filter = ('author',)
    inlines = (WordTranslationInline,)


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

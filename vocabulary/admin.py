''' Vocabulary admin config '''

from django.contrib import admin

from .models import (Antonym, Collection, Definition, FavoriteCollection,
                     FavoriteWord, Form, ImageAssociation, Note, Similar,
                     Synonym, Tag, Translation, Type, UsageExample, Word,
                     WordDefinitions, WordsInCollections, WordTranslations,
                     WordUsageExamples)


class WordAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('text', 'author')}


class CollectionAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title', 'author')}


admin.site.register(Word, WordAdmin)
admin.site.register(Collection, CollectionAdmin)
admin.site.register(Translation)
admin.site.register(WordTranslations)
admin.site.register(UsageExample)
admin.site.register(WordUsageExamples)
admin.site.register(Definition)
admin.site.register(WordDefinitions)
admin.site.register(Tag)
admin.site.register(Type)
admin.site.register(WordsInCollections)
admin.site.register(Synonym)
admin.site.register(Antonym)
admin.site.register(Form)
admin.site.register(Similar)
admin.site.register(Note)
admin.site.register(ImageAssociation)
admin.site.register(FavoriteWord)
admin.site.register(FavoriteCollection)

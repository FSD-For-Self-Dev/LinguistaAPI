''' Vocabulary admin config '''

from django.contrib import admin

from .models import (Collection, Definition, FavoriteCollection, FavoriteWord,
                     Note, Synonyms, Tag, Translation, Type, UsageExample,
                     Word, WordDefinitions, WordsInCollections,
                     WordTranslations, WordUsageExamples)

admin.site.register(Word)
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
admin.site.register(Synonyms)
admin.site.register(Note)
admin.site.register(FavoriteWord)
admin.site.register(FavoriteCollection)

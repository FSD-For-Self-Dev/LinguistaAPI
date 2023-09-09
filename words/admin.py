"""Административные настройки приложения words."""

from django.contrib import admin

from .models import (Collection, Exercise, Tag, Translation,  # Synonym
                     UsageExample, Word)


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    list_display = ('text', 'author',
                    'status', 'type',
                    'language'
                    )
    order_display = ('status',)




admin.site.register(Translation)
admin.site.register(UsageExample)
admin.site.register(Tag)
# admin.site.register(Synonym)
admin.site.register(Collection)
admin.site.register(Exercise)

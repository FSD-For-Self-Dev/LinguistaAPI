""" Vocabulary admin config """

from django.contrib import admin

from .models import (Collection, Exercise, Tag, Translation,  # Synonym
                     UsageExample, Word)

admin.site.register(Word)
admin.site.register(Translation)
admin.site.register(UsageExample)
admin.site.register(Tag)
# admin.site.register(Synonym)
admin.site.register(Collection)
admin.site.register(Exercise)

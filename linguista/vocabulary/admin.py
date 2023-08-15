''' Vocabulary admin config '''

from django.contrib import admin

from .models import (Collection, Tag, Translation, Type,
                     UsageExample, Word)

admin.site.register(Word)
admin.site.register(Translation)
admin.site.register(UsageExample)
admin.site.register(Tag)
admin.site.register(Type)
admin.site.register(Collection)

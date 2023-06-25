from django.contrib import admin

from .models import Word, Collection, Exercise


admin.site.register(Word)
admin.site.register(Collection)
admin.site.register(Exercise)

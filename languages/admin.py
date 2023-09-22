''' Languages admin config '''

from django.contrib import admin

from .models import Language, UserLanguage

admin.site.register(Language)
admin.site.register(UserLanguage)

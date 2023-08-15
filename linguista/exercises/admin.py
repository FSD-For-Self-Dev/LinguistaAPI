''' Exercises admin config '''

from django.contrib import admin

from .models import Exercise


admin.site.register(Exercise)

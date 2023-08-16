''' Exercises admin config '''

from django.contrib import admin

from .models import Exercise, FavoriteExercise

admin.site.register(Exercise)
admin.site.register(FavoriteExercise)

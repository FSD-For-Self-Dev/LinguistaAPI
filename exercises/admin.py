"""Exercises admin config."""

from django.contrib import admin

from .models import (
    Exercise,
    FavoriteExercise,
    Hint,
    WordSet,
    UsersExercisesHistory,
    TranslatorHistoryDetails,
    TranslatorUserDefaultSettings,
    WordsUpdateHistory,
)


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'description')
    list_display_links = ('name',)
    search_fields = ('name',)


admin.site.register(FavoriteExercise)
admin.site.register(Hint)
admin.site.register(WordSet)
admin.site.register(UsersExercisesHistory)
admin.site.register(TranslatorHistoryDetails)
admin.site.register(TranslatorUserDefaultSettings)
admin.site.register(WordsUpdateHistory)

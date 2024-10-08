"""Exercises app admin panel."""

from django.contrib import admin

from .models import (
    Exercise,
    FavoriteExercise,
    Hint,
    WordSet,
    UsersExercisesHistory,
    ExerciseHistoryDetails,
    TranslatorUserDefaultSettings,
    WordsUpdateHistory,
)


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'description')
    list_display_links = ('name',)
    search_fields = ('name',)


@admin.register(FavoriteExercise)
class FavoriteExerciseAdmin(admin.ModelAdmin):
    pass


@admin.register(Hint)
class HintAdmin(admin.ModelAdmin):
    pass


@admin.register(WordSet)
class WordSetAdmin(admin.ModelAdmin):
    pass


@admin.register(UsersExercisesHistory)
class UsersExercisesHistoryAdmin(admin.ModelAdmin):
    pass


@admin.register(ExerciseHistoryDetails)
class ExerciseHistoryDetailsAdmin(admin.ModelAdmin):
    pass


@admin.register(TranslatorUserDefaultSettings)
class TranslatorUserDefaultSettingsAdmin(admin.ModelAdmin):
    pass


@admin.register(WordsUpdateHistory)
class WordsUpdateHistoryAdmin(admin.ModelAdmin):
    pass

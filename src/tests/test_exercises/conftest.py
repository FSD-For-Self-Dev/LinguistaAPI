import pytest

from model_bakery import baker

from apps.exercises.models import Exercise, UsersExercisesHistory, WordSet


@pytest.fixture
def exercises(request):
    def get_exercises(data=False, extra_data={}, _quantity=1, **kwargs):
        exercises = baker.make(
            Exercise, **extra_data, _quantity=_quantity, _fill_optional=True
        )
        return exercises

    return get_exercises


@pytest.fixture
def exercise_history(request):
    def get_exercise_history(data=False, extra_data={}, _quantity=1, **kwargs):
        exercise_history = baker.make(
            UsersExercisesHistory,
            **extra_data,
            _quantity=_quantity,
            _fill_optional=True,
        )
        return exercise_history

    return get_exercise_history


@pytest.fixture
def word_sets(request):
    def get_word_sets(data=False, make=True, extra_data={}, _quantity=1, **kwargs):
        if make:
            word_sets = baker.make(
                WordSet, **extra_data, _quantity=_quantity, _fill_optional=True
            )
        else:
            word_sets = baker.prepare(
                WordSet, **extra_data, _quantity=_quantity, _fill_optional=True
            )
        if data:
            source_data = [
                {
                    'name': word_set.name,
                }
                for word_set in word_sets
            ]
            expected_data = source_data
            return (word_sets, source_data, expected_data)
        return word_sets

    return get_word_sets

"""Фильтры приложения vocabulary."""

import django_filters as df
from django.db.models import Q

from .models import Collection, Word


class CollectionFilter(df.FilterSet):
    """Фильтры коллекций."""

    words_count__gt = df.NumberFilter(field_name='words_count', lookup_expr='gt')
    words_count__lt = df.NumberFilter(field_name='words_count', lookup_expr='lt')

    class Meta:
        model = Collection
        fields = {
            'created': [
                'exact',
                'gt',
                'lt',
                'year',
                'year__gt',
                'year__lt',
                'month',
                'month__gt',
                'month__lt',
            ],
        }


class CustomFilterList(df.Filter):
    """Фильтрация по списку значений."""

    def filter(self, qs, value):
        if value not in (None, ''):
            values = [v for v in value.split(',')]
            return qs.filter(**{'%s__%s' % (self.field_name, self.lookup_expr): values})
        return qs


class WordFilter(df.FilterSet):
    """Фильтры слов."""

    language = df.CharFilter(field_name='language__isocode')
    is_problematic = df.BooleanFilter(field_name='is_problematic')
    tags = CustomFilterList(field_name='tags__name', lookup_expr='in')
    activity_status = df.ChoiceFilter(choices=Word.ACTIVITY)
    types = CustomFilterList(field_name='types__slug', lookup_expr='in')
    first_letter = df.CharFilter(field_name='text', lookup_expr='istartswith')
    have_associations = df.BooleanFilter(method='filter_have_associations')
    translations_count = df.NumberFilter(
        field_name='translations_count', lookup_expr='exact'
    )
    translations_count__gt = df.NumberFilter(
        field_name='translations_count', lookup_expr='gt'
    )
    translations_count__lt = df.NumberFilter(
        field_name='translations_count', lookup_expr='lt'
    )
    examples_count = df.NumberFilter(field_name='examples_count', lookup_expr='exact')
    examples_count__gt = df.NumberFilter(field_name='examples_count', lookup_expr='gt')
    examples_count__lt = df.NumberFilter(field_name='examples_count', lookup_expr='lt')

    class Meta:
        model = Word
        fields = {
            'created': [
                'date',
                'date__gt',
                'date__lt',
                'year',
                'year__gt',
                'year__lt',
                'month',
                'month__gt',
                'month__lt',
            ],
            'last_exercise_date': [
                'date',
                'date__gt',
                'date__lt',
                'year',
                'year__gt',
                'year__lt',
                'month',
                'month__gt',
                'month__lt',
            ],
        }

    def filter_have_associations(self, queryset, name, value):
        if value:
            return queryset.filter(
                Q(images_associations__isnull=False)
                | Q(quotes_associations__isnull=False)
            )
        else:
            return queryset.filter(
                Q(images_associations__isnull=True)
                & Q(quotes_associations__isnull=True)
            )

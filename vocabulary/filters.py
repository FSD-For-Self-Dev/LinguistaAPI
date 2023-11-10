"""Фильтры приложения vocabulary."""

import django_filters as df
from .models import Collection, Word


class CollectionFilter(df.FilterSet):
    """Фильтры коллекций."""

    words_count__gt = df.NumberFilter(field_name='words_count',
                                       lookup_expr='gt')
    words_count__lt = df.NumberFilter(field_name='words_count',
                                       lookup_expr='lt')

    class Meta:
        model = Collection


class CustomFilterList(df.Filter):
    """Фильтрация по списку значений."""

    def filter(self, qs, value):
        if value not in (None, ''):
            values = [v for v in value.split(',')]
            return qs.filter(**{'%s__%s' %
                                (self.field_name, self.lookup_expr): values})
        return qs


class WordFilter(df.FilterSet):
    """Фильтры слов."""

    language = df.CharFilter(field_name='language__isocode')
    is_problematic = df.BooleanFilter(field_name='is_problematic')
    tags = CustomFilterList(
        field_name='tags__name', lookup_expr='in'
    )
    activity = df.ChoiceFilter(choices=Word.ACTIVITY)
    types = CustomFilterList(
        field_name='types__slug', lookup_expr='in'
    )
    first_letter = df.CharFilter(field_name='text', lookup_expr='istartswith')
    # have_associations = df.BooleanFilter(method='filter_have_associations')
    translations_count = df.NumberFilter(
        field_name='translations_count',
        lookup_expr='exact'
    )
    translations_count__gt = df.NumberFilter(
        field_name='translations_count',
        lookup_expr='gt'
    )
    translations_count__lt = df.NumberFilter(
        field_name='translations_count',
        lookup_expr='lt'
    )
    examples_count = df.NumberFilter(
        field_name='examples_count',
        lookup_expr='exact'
    )
    examples_count__gt = df.NumberFilter(
        field_name='examples_count',
        lookup_expr='gt'
    )
    examples_count__lt = df.NumberFilter(
        field_name='examples_count',
        lookup_expr='lt'
    )

    class Meta:
        model = Word
        fields = {
            'created': [
                'exact', 'gt', 'lt', 'year', 'year__gt', 'year__lt',
                'month', 'month__gt', 'month__lt'
            ],
        }

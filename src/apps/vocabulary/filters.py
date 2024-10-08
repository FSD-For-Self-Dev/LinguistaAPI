"""Vocabulary app filters."""

import django_filters as df
from django.db.models import Q
from django.db.models.query import QuerySet

from .models import Collection, Word


class CollectionFilter(df.FilterSet):
    """Filters for collections."""

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
    """Filtering by multiple comma-separated values."""

    def filter(self, qs: QuerySet, value: str) -> QuerySet:
        if value not in (None, ''):
            values = [v for v in value.split(',')]
            return qs.filter(**{'%s__%s' % (self.field_name, self.lookup_expr): values})
        return qs


class WordFilter(df.FilterSet):
    """Filters for words."""

    language = df.CharFilter(field_name='language__isocode')
    is_problematic = df.BooleanFilter(field_name='is_problematic')
    tags = CustomFilterList(field_name='tags__name', lookup_expr='in')
    activity_status = df.ChoiceFilter(choices=Word.ACTIVITY)
    types = CustomFilterList(field_name='types__slug', lookup_expr='in')
    first_letter = df.CharFilter(field_name='text', lookup_expr='istartswith')
    last_letter = df.CharFilter(field_name='text', lookup_expr='endswith')
    have_associations = df.BooleanFilter(method='filter_have_associations')
    translations_count = df.NumberFilter(
        field_name='translations_count',
        lookup_expr='exact',
    )
    translations_count__gt = df.NumberFilter(
        field_name='translations_count',
        lookup_expr='gt',
    )
    translations_count__lt = df.NumberFilter(
        field_name='translations_count',
        lookup_expr='lt',
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

    def filter_have_associations(
        self, queryset: QuerySet, name: str, value: str
    ) -> QuerySet:
        """
        Returns words that have at least one association of any type if True is
        passed, returns words with no associations if False if passed.
        """
        if value:
            return queryset.filter(
                Q(image_associations__isnull=False)
                | Q(quote_associations__isnull=False)
            )
        else:
            return queryset.filter(
                Q(image_associations__isnull=True) & Q(quote_associations__isnull=True)
            )

"""Vocabulary app filters."""

import django_filters as df
from django.db.models import Q, Count
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


class CustomFilterListLowerCase(df.Filter):
    """Filtering by multiple comma-separated lowercase values."""

    def filter(self, qs: QuerySet, value: str) -> QuerySet:
        if value not in (None, ''):
            values = [v.lower() for v in value.split(',')]
            return qs.filter(**{'%s__%s' % (self.field_name, self.lookup_expr): values})
        return qs


class WordFilter(df.FilterSet):
    """Filters for words."""

    language = df.CharFilter(field_name='language__isocode')
    is_problematic = df.BooleanFilter(field_name='is_problematic')
    tags = CustomFilterListLowerCase(field_name='tags__name', lookup_expr='in')
    activity_status = df.ChoiceFilter(choices=Word.ACTIVITY)
    types = CustomFilterList(field_name='types__slug', lookup_expr='in')
    first_letter = df.CharFilter(field_name='text', lookup_expr='istartswith')
    last_letter = df.CharFilter(field_name='text', lookup_expr='endswith')
    have_associations = df.BooleanFilter(method='filter_have_associations')

    # amount filters
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

    definitions_count = df.NumberFilter(
        field_name='definitions_count',
        lookup_expr='exact',
    )
    definitions_count__gt = df.NumberFilter(
        field_name='definitions_count',
        lookup_expr='gt',
    )
    definitions_count__lt = df.NumberFilter(
        field_name='definitions_count',
        lookup_expr='lt',
    )

    image_associations_count = df.NumberFilter(
        field_name='image_associations_count',
        lookup_expr='exact',
    )
    image_associations_count__gt = df.NumberFilter(
        field_name='image_associations_count',
        lookup_expr='gt',
    )
    image_associations_count__lt = df.NumberFilter(
        field_name='image_associations_count',
        lookup_expr='lt',
    )

    synonyms_count = df.NumberFilter(field_name='synonyms_count', lookup_expr='exact')
    synonyms_count__gt = df.NumberFilter(field_name='synonyms_count', lookup_expr='gt')
    synonyms_count__lt = df.NumberFilter(field_name='synonyms_count', lookup_expr='lt')

    antonyms_count = df.NumberFilter(field_name='antonyms_count', lookup_expr='exact')
    antonyms_count__gt = df.NumberFilter(field_name='antonyms_count', lookup_expr='gt')
    antonyms_count__lt = df.NumberFilter(field_name='antonyms_count', lookup_expr='lt')

    forms_count = df.NumberFilter(field_name='forms_count', lookup_expr='exact')
    forms_count__gt = df.NumberFilter(field_name='forms_count', lookup_expr='gt')
    forms_count__lt = df.NumberFilter(field_name='forms_count', lookup_expr='lt')

    similars_count = df.NumberFilter(field_name='similars_count', lookup_expr='exact')
    similars_count__gt = df.NumberFilter(field_name='similars_count', lookup_expr='gt')
    similars_count__lt = df.NumberFilter(field_name='similars_count', lookup_expr='lt')

    tags_count = df.NumberFilter(field_name='tags_count', lookup_expr='exact')
    tags_count__gt = df.NumberFilter(field_name='tags_count', lookup_expr='gt')
    tags_count__lt = df.NumberFilter(field_name='tags_count', lookup_expr='lt')

    types_count = df.NumberFilter(field_name='types_count', lookup_expr='exact')
    types_count__gt = df.NumberFilter(field_name='types_count', lookup_expr='gt')
    types_count__lt = df.NumberFilter(field_name='types_count', lookup_expr='lt')

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


class WordCounters:
    translations_count = Count('translations', distinct=True)
    examples_count = Count('examples', distinct=True)
    definitions_count = Count('definitions', distinct=True)
    image_associations_count = Count('image_associations', distinct=True)
    quote_associations_count = Count('quote_associations', distinct=True)
    synonyms_count = Count('synonyms', distinct=True)
    antonyms_count = Count('antonyms', distinct=True)
    forms_count = Count('forms', distinct=True)
    similars_count = Count('similars', distinct=True)
    tags_count = Count('tags', distinct=True)
    types_count = Count('types', distinct=True)
    collections_count = Count('collections', distinct=True)

    all = {
        'translations_count': translations_count,
        'examples_count': examples_count,
        'definitions_count': definitions_count,
        'image_associations_count': image_associations_count,
        'quote_associations_count': quote_associations_count,
        'synonyms_count': synonyms_count,
        'antonyms_count': antonyms_count,
        'forms_count': forms_count,
        'similars_count': similars_count,
        'tags_count': tags_count,
        'types_count': types_count,
        'collections_count': collections_count,
    }

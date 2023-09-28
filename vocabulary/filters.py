import django_filters as df
from django.db.models import Count
from vocabulary.models import Word


class WordFilter(df.FilterSet):
    language = df.CharFilter(field_name='language__isocode')
    is_problematic = df.BooleanFilter(field_name='is_problematic')
    tags = df.CharFilter(method='filter_tags')
    activity = df.ChoiceFilter(choices=Word.ACTIVITY)
    type = df.CharFilter(field_name='type__name')
    date_added = df.DateFilter(field_name='created', lookup_expr='exact')
    date_added__gt = df.DateFilter(field_name='created', lookup_expr='gt')
    date_added__lt = df.DateFilter(field_name='created', lookup_expr='lt')
    first_letter = df.CharFilter(field_name='text', lookup_expr='istartswith')
    have_associations = df.BooleanFilter(method='filter_have_associations')
    translations_amount = df.NumberFilter(method='filter_translations_amount',
                                          lookup_expr='exact')
    translations_amount__gt = df.NumberFilter(
        method='filter_translations_amount', lookup_expr='gt')
    translations_amount__lt = df.NumberFilter(
        method='filter_translations_amount', lookup_expr='lt')
    examples_amount = df.NumberFilter(method='filter_examples_amount')
    examples_amount__gt = df.NumberFilter(method='filter_examples_amount',
                                          lookup_expr='gt')
    examples_amount__lt = df.NumberFilter(method='filter_examples_amount',
                                          lookup_expr='lt')

    def filter_tags(self, queryset, name, value):
        if value:
            tags = value.split(',')
            return queryset.filter(tags__name__in=tags)
        return queryset

    def filter_have_associations(self, queryset, name, value):
        if value:
            return queryset.filter(synonyms__isnull=False) | queryset.filter(
                antonyms__isnull=False) | queryset.filter(
                forms__isnull=False) | queryset.filter(similars__isnull=False)
        return queryset

    def filter_translations_amount(self, queryset, name, value):
        filter = {name: value}
        if value:
            return queryset.annotate(
                translations_amount=Count('translations',
                                          distinct=True)).filter(**filter)
        return queryset

    def filter_examples_amount(self, queryset, name, value):
        filter = {name: value}
        if value:
            queryset.annotate(
                examples_amount=Count('examples',
                                      distinct=True)).filter(**filter)
        return queryset

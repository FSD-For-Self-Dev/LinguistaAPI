"""Команда для импорта возможныз типов слов и фраз."""

from django.core.management.base import BaseCommand, CommandError

from vocabulary.models import Type

TYPE_CHOICES = [
    ('NOUN', 'Noun', 3),
    ('VERB', 'Verb', 3),
    ('ADJECT', 'Adjective', 3),
    ('ADVERB', 'Adverb', 2),
    ('PRONOUN', 'Pronoun', 1),
    ('PREPOS', 'Preposition', 2),
    ('UNION', 'Union', 1),
    ('PARTICLE', 'Particle', 1),
    ('PARTICIPLE', 'Participle', 2),
    ('GERUND', 'Gerund', 2),
    ('ARTICLE', 'Article', 1),
    ('PREDICATIVE', 'Predicative', 1),
    ('NUMERAL', 'Numeral', 2),
    ('INTERJ', 'Interjection', 1),
    ('PHRASE', 'Phrase', 3),
    ('IDIOM', 'Idiom', 1),
    ('QUOTE', 'Quote', 2),
    ('Collocation', 'Collocation', 3),
    ('PROVERB', 'Proverb', 1),
]


class Command(BaseCommand):
    """
    Command to import possible word types from TYPE_CHOICES
    """

    help = ('Imports possible word types names, slugs from '
            'TYPE_CHOICES')

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        self.stdout.write('Importing types...')
        cnt = 0
        for type_info in TYPE_CHOICES:
            try:
                word_type, created = Type.objects.get_or_create(
                    slug=type_info[0].lower(),
                    name=type_info[1],
                    sorting=type_info[2]
                )
                if created:
                    cnt += 1
            except Exception as e:
                raise CommandError(
                    'Error adding type %s{type}: %s{error}'.format(
                        type=word_type, error=e
                    )
                )
        self.stdout.write('Added %d types' % cnt)

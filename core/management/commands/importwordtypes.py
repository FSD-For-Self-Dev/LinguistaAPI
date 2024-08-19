"""Команда для импорта возможныз типов слов и фраз."""

from django.core.management.base import BaseCommand

from tqdm import tqdm

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

    help = 'Imports possible word types names, slugs from ' 'TYPE_CHOICES'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        cnt = 0
        for type_info in tqdm(TYPE_CHOICES, desc='Importing types'):
            try:
                type, created = Type.objects.get_or_create(
                    name=type_info[1],
                )
                if created:
                    cnt += 1
            except Exception as e:
                self.stdout.write(f'Error adding type: {e}')
        self.stdout.write('Added %d types' % cnt)

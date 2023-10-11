''' Custom command to import possible word types '''

from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import gettext_lazy as _

from vocabulary.models import Type

TYPE_CHOICES = [
    ('NOUN', _('Noun'), 3),
    ('VERB', _('Verb'), 3),
    ('ADJECT', _('Adjective'), 3),
    ('ADVERB', _('Adverb'), 2),
    ('PRONOUN', _('Pronoun'), 1),
    ('PREPOS', _('Preposition'), 2),
    ('UNION', _('Union'), 1),
    ('PARTICLE', _('Particle'), 1),
    ('PARTICIPLE', _('Participle'), 2),
    ('GERUND', _('Gerund'), 2),
    ('ARTICLE', _('Article'), 1),
    ('PREDICATIVE', _('Predicative'), 1),
    ('NUMERAL', _('Numeral'), 2),
    ('INTERJ', _('Interjection'), 1),
    ('PHRASE', _('Phrase'), 3),
    ('IDIOM', _('Idiom'), 1),
    ('QUOTE', _('Quote'), 2),
    ('Collocation', _('Collocation'), 3),
    ('PROVERB', _('Proverb'), 1),
]


class Command(BaseCommand):
    '''
    Command to import possible word types from TYPE_CHOICES
    '''

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

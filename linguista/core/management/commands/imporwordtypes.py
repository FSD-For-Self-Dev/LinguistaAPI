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
    ('IDIOM', _('Idiom'), 2),
    ('QUOTE', _('Quote'), 3),
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
        if not Type.objects.exists():
            self.stdout.write('Types not found, creating ones...')
            cnt = 0
            for type_info in TYPE_CHOICES:
                try:
                    word_type = Type(
                        slug=type_info[0].lower(),
                        name=type_info[1],
                        sorting=type_info[2]
                    )
                    word_type.save()
                    cnt += 1
                except Exception as e:
                    raise CommandError(
                        'Error adding type %s{type}: %s{error}'.format(
                            type=word_type, error=e
                        )
                    )
            self.stdout.write('Added %d types' % cnt)
        else:
            self.stdout.write('Types were found, exiting')

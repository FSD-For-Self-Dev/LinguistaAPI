''' Custom command to import languages '''

from django.conf.locale import LANG_INFO
from django.core.management.base import BaseCommand, CommandError

from core.constants import LANGS_SORTING_VALS
from core.models import Language


class Command(BaseCommand):
    '''
    Command to import languages from django.conf.locale.LANG_INFO
    '''

    help = ('Imports language codes and names from '
            'django.conf.locale.LANG_INFO')

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        self.stdout.write('Importing languages...')
        cnt = 0
        for isocode in LANG_INFO:
            # we only care about the 2 letter iso codes
            if len(isocode) == 2:
                try:
                    lang, created = Language.objects.get_or_create(
                        isocode=isocode,
                        name=LANG_INFO[isocode]['name'],
                        name_local=LANG_INFO[isocode]['name_local']
                    )
                    lang.sorting = LANGS_SORTING_VALS.get(lang.isocode, 0)
                    lang.save()
                    if created:
                        cnt += 1
                except Exception as e:
                    raise CommandError(
                        'Error adding language %s: %s' % (lang, e)
                    )
        self.stdout.write('Added %d languages to users' % cnt)

"""Custom command to import languages."""

import os

from django.conf.locale import LANG_INFO
from django.core.management.base import BaseCommand, CommandError
from django.core.files.images import ImageFile

from tqdm import tqdm

from languages.models import Language, LanguageImage


class Command(BaseCommand):
    """
    Command to import languages from django.conf.locale.LANG_INFO.
    """

    help = 'Imports language codes and names from ' 'django.conf.locale.LANG_INFO'
    images_path = 'languages/images/'
    flag_icons_path = 'languages/images/flag_icons/'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        cnt = 0
        for isocode in tqdm(LANG_INFO, desc='Importing languages'):
            # we only care about the 2 letter iso codes
            if len(isocode) == 2:
                try:
                    lang, created = Language.objects.get_or_create(
                        isocode=isocode,
                        name=LANG_INFO[isocode]['name'],
                        name_local=LANG_INFO[isocode]['name_local'],
                    )
                    lang.sorting = Language.LANGS_SORTING_VALS.get(isocode, 0)
                    lang.learning_available = Language.LEARN_AVAILABLE.get(
                        isocode, False
                    )
                    lang.interface_available = Language.INTERFACE_AVAILABLE.get(
                        isocode, False
                    )
                    try:
                        flag_icon_url = self.flag_icons_path + isocode + '.svg'
                        flag_icon = ImageFile(open(flag_icon_url, 'rb'))
                        lang.flag_icon = flag_icon
                    except FileNotFoundError:
                        pass
                    lang.save()
                    if created:
                        cnt += 1
                    if lang.learning_available:
                        images_urls = [
                            self.images_path + filename
                            for filename in os.listdir(self.images_path)
                            if filename.startswith(lang.isocode)
                        ]
                        for image_url in images_urls:
                            image = ImageFile(open(image_url, 'rb'))
                            LanguageImage.objects.create(language=lang, image=image)
                except Exception as e:
                    raise CommandError('Error adding language %s: %s' % (lang, e))
        self.stdout.write('Added %d languages' % cnt)

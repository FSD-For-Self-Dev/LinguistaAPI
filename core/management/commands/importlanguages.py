"""Custom command to import languages."""

import os
from tqdm import tqdm

from django.conf.locale import LANG_INFO
from django.core.management.base import BaseCommand
from django.core.files.images import ImageFile


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

                    if created:
                        cnt += 1

                        try:
                            flag_icon_url = self.flag_icons_path + isocode + '.svg'
                            flag_icon = ImageFile(open(flag_icon_url, 'rb'))
                            flag_icon.name = isocode + '.svg'
                            lang.flag_icon = flag_icon
                        except FileNotFoundError:
                            self.stdout.write(f'Flag icon not found: {lang}')

                        if lang.learning_available:
                            images_urls = [
                                self.images_path + filename
                                for filename in os.listdir(self.images_path)
                                if filename.startswith(lang.isocode)
                            ]
                            for image_url in images_urls:
                                image = ImageFile(open(image_url, 'rb'))
                                image.name = isocode + '.' + image.name.split('.')[-1]
                                LanguageImage.objects.create(language=lang, image=image)

                    lang.save()

                except Exception as e:
                    self.stdout.write(f'Error adding language: {e}')

        self.stdout.write('Added %d languages' % cnt)

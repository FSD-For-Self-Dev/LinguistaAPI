"""Custom command to import languages."""

import os
import requests
import logging
import json
from tqdm import tqdm

from django.core.management.base import BaseCommand
from django.core.files.images import ImageFile

from dotenv import load_dotenv
from modeltranslation.translator import translator

from apps.languages.models import Language, LanguageCoverImage, UserLearningLanguage
from utils.getters import get_yc_headers, get_admin_user
from config.settings import LANGUAGES
from .data.languages import TWO_LETTERS_CODES_V3

load_dotenv()

logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)


class Command(BaseCommand):
    """
    Command to import languages from django.conf.locale.LANG_INFO.
    """

    help = 'Imports language codes and names from ' 'django.conf.locale.LANG_INFO'

    images_path = 'apps/languages/images/'
    flag_icons_path = 'apps/languages/images/flag_icons/'

    translator_url = 'https://translate.api.cloud.yandex.net/translate/v2/translate'
    languages_source_language_code = 'en'

    def add_arguments(self, parser):
        parser.add_argument(
            '--import_images',
            action='store_true',
            default=False,
            help='Pass if images import is needed no matter languages exist',
        )
        parser.add_argument(
            '--add_translations',
            action='store_true',
            default=False,
            help='Pass if languages fields translations is needed no matter languages exist',
        )
        parser.add_argument(
            '--all_available',
            action='store_true',
            default=False,
            help='Pass to make all languages available for learning',
        )
        parser.add_argument(
            '--only_popular',
            action='store_true',
            default=False,
            help='Pass to make only languages with sorting value more than 0 available for learning',
        )
        parser.add_argument(
            'last_locales',
            type=int,
            nargs='?',
            help='For example, if the value 1 is passed, the fields will be translated only to the last locale language',
        )

    def handle(self, *args, **options):
        cnt = 0
        skip_cnt = 0
        for isocode in tqdm(TWO_LETTERS_CODES_V3, desc='Importing languages'):
            try:
                if not TWO_LETTERS_CODES_V3[isocode]['name_local']:
                    skip_cnt += 1
                    continue
                try:
                    lang = Language.objects.get(isocode=isocode.lower())
                    created = False
                except Language.DoesNotExist:
                    lang = Language.objects.create(
                        isocode=isocode.lower(),
                        name=TWO_LETTERS_CODES_V3[isocode]['name'],
                        name_local=TWO_LETTERS_CODES_V3[isocode]['name_local'],
                        country=TWO_LETTERS_CODES_V3[isocode]['country'],
                    )
                    created = True

                lang.sorting = Language.LANGS_SORTING_VALS.get(isocode.lower(), 0)
                all_available = options['all_available']
                only_popular = options['only_popular']
                lang.learning_available = (
                    lang.sorting > 0
                    if only_popular
                    else (
                        True
                        if all_available
                        else Language.LEARN_AVAILABLE.get(isocode.lower(), False)
                    )
                )
                lang.interface_available = Language.INTERFACE_AVAILABLE.get(
                    isocode.lower(), False
                )

                if created:
                    cnt += 1

                # Translating specified fields into locales from config
                add_translations = options['add_translations']
                last_locales = options['last_locales']
                locales = LANGUAGES[::-1][:last_locales] if last_locales else LANGUAGES
                if add_translations:
                    for field in translator.get_options_for_model(Language).fields:
                        for locale in locales:
                            locale_isocode, _ = locale
                            if locale_isocode == self.languages_source_language_code:
                                continue
                            request_data = json.dumps(
                                {
                                    'folderId': os.getenv('YC_FOLDER_ID', default=''),
                                    'sourceLanguageCode': self.languages_source_language_code,
                                    'targetLanguageCode': locale_isocode,
                                    'texts': [TWO_LETTERS_CODES_V3[isocode][field]],
                                }
                            )
                            response = requests.post(
                                self.translator_url,
                                headers=get_yc_headers(),
                                data=request_data,
                            )
                            try:
                                if response.status_code == 200:
                                    response_content = response.json()
                                    lang.__setattr__(
                                        f'{field}_{locale_isocode}',
                                        response_content['translations'][0]['text'],
                                    )
                                else:
                                    response_content = response.json()
                                    self.stdout.write(
                                        f'Error occured: translator (url: {self.translator_url}) '
                                        f'returned {response.status_code} status code: {response_content}'
                                    )
                            except Exception as e:
                                self.stdout.write(
                                    f'Error occured: translator (url: {self.translator_url}): '
                                    f'{e}'
                                )

                # Importing specified flag icons, images for languages
                import_images = options['import_images']
                if created or import_images:
                    # Importing flag icons
                    try:
                        flag_icon_path = TWO_LETTERS_CODES_V3[isocode]['flag_icon_path']
                        flag_icon = ImageFile(open(flag_icon_path, 'rb'))
                        flag_icon.name = isocode + '.svg'
                        lang.flag_icon = flag_icon
                    except FileNotFoundError:
                        self.stdout.write(
                            f'\nFlag icon not found: {lang.name} ({lang.country})'
                        )
                        flag_icon_path = self.flag_icons_path + 'world' + '.svg'
                        flag_icon = ImageFile(open(flag_icon_path, 'rb'))
                        flag_icon.name = isocode + '.svg'
                        lang.flag_icon = flag_icon

                    # Importing covers images for learning available languages
                    if lang.learning_available:
                        admin_user = get_admin_user()
                        LanguageCoverImage.objects.filter(
                            language=lang, author=admin_user
                        ).delete()
                        images_urls = [
                            self.images_path + filename
                            for filename in os.listdir(self.images_path)
                            if filename.startswith(lang.isocode)
                        ]
                        images_cnt = 0
                        for image_url in images_urls:
                            image = ImageFile(open(image_url, 'rb'))
                            image.name = isocode + '.' + image.name.split('.')[-1]
                            lang_cover = LanguageCoverImage.objects.create(
                                language=lang, image=image, author=admin_user
                            )
                            # Setting default cover image
                            if images_cnt == 0:
                                UserLearningLanguage.objects.filter(
                                    language=lang
                                ).update(cover=lang_cover)
                                images_cnt += 1

                lang.save()

            except Exception as e:
                self.stdout.write(
                    f'Error adding language {lang} (isocode: {lang.isocode}): {e}'
                )

        self.stdout.write(
            f'Added {cnt} languages\nSkipped {skip_cnt} languages (empty `name_local` value)'
        )

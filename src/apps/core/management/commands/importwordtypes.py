"""Команда для импорта возможныз типов слов и фраз."""

import os
import requests
import logging
import json
from tqdm import tqdm

from django.core.management.base import BaseCommand

from dotenv import load_dotenv
from modeltranslation.translator import translator

from apps.vocabulary.models import WordType
from utils.getters import get_yc_headers
from config.settings import LANGUAGES

load_dotenv()

logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

TYPE_CHOICES = [
    {
        'name': 'Noun',
        'sorting': 3,
    },
    {
        'name': 'Verb',
        'sorting': 3,
    },
    {
        'name': 'Adjective',
        'sorting': 3,
    },
    {
        'name': 'Adverb',
        'sorting': 2,
    },
    {
        'name': 'Pronoun',
        'sorting': 1,
    },
    {
        'name': 'Preposition',
        'sorting': 2,
    },
    {
        'name': 'Union',
        'sorting': 1,
    },
    {
        'name': 'Particle',
        'sorting': 1,
    },
    {
        'name': 'Participle',
        'sorting': 2,
    },
    {
        'name': 'Gerund',
        'sorting': 2,
    },
    {
        'name': 'Article',
        'sorting': 1,
    },
    {
        'name': 'Predicative',
        'sorting': 1,
    },
    {
        'name': 'Numeral',
        'sorting': 2,
    },
    {
        'name': 'Interjection',
        'sorting': 1,
    },
    {
        'name': 'Phrase',
        'sorting': 3,
    },
    {
        'name': 'Idiom',
        'sorting': 1,
    },
    {
        'name': 'Quote',
        'sorting': 2,
    },
    {
        'name': 'Collocation',
        'sorting': 3,
    },
    {
        'name': 'Proverb',
        'sorting': 1,
    },
]


class Command(BaseCommand):
    """
    Command to import possible word types from TYPE_CHOICES
    """

    help = 'Imports possible word types names, slugs from ' 'TYPE_CHOICES'

    translator_url = 'https://translate.api.cloud.yandex.net/translate/v2/translate'
    languages_source_language_code = 'en'

    def add_arguments(self, parser):
        parser.add_argument(
            '--add_translations',
            action='store_true',
            default=False,
            help='Pass if types fields translations is needed no matter types exist',
        )
        parser.add_argument(
            'last_locales',
            type=int,
            nargs='?',
            help='For example, if the value 1 is passed, the fields will be translated only to the last locale language',
        )

    def handle(self, *args, **options):
        cnt = 0

        for type_info in tqdm(TYPE_CHOICES, desc='Importing types'):
            try:
                wordtype, created = WordType.objects.get_or_create(
                    name=type_info['name'],
                )

                if created:
                    cnt += 1

                # Translating specified fields into locales from config
                add_translations = options['add_translations']
                last_locales = options['last_locales']
                locales = LANGUAGES[::-1][:last_locales] if last_locales else LANGUAGES
                if add_translations:
                    for field in translator.get_options_for_model(WordType).fields:
                        for locale in locales:
                            locale_isocode, _ = locale
                            if locale_isocode == self.languages_source_language_code:
                                continue
                            request_data = json.dumps(
                                {
                                    'folderId': os.getenv('YC_FOLDER_ID', default=''),
                                    'sourceLanguageCode': self.languages_source_language_code,
                                    'targetLanguageCode': locale_isocode,
                                    'texts': [type_info[field]],
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
                                    wordtype.__setattr__(
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

                wordtype.save()

            except Exception as e:
                self.stdout.write(f'Error adding type: {e}')

        self.stdout.write('Added %d types' % cnt)

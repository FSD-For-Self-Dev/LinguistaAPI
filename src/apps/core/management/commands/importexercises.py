"""Custom command to import exercises."""

from django.core.management.base import BaseCommand, CommandError
from django.core.files.images import ImageFile

from tqdm import tqdm

from apps.exercises.models import Exercise, Hint
from apps.exercises.constants import exercises_lookups


class Command(BaseCommand):
    """Command to import exercises."""

    help = 'Imports exercises'
    icons_path = 'exercises/icons/'

    EXERCISES_INFO = {
        'tr': {
            'name': 'Translator',
            'slug': exercises_lookups.TRANSLATOR_EXERCISE_SLUG,
            'description': (
                'Translate a word on time or in free mode from your native '
                'language to the language you are learning and vice versa.'
            ),
            'available': True,
            'constraint_description': 'Only words with translations.',
            'hints_available': [
                'show_association',
                'show_first_letter',
                'show_letters_amount',
                'show_synonym',
                'remove_incorrect',
            ],
        },
        'as': {
            'name': 'Associate',
            'slug': exercises_lookups.ASSOCIATE_EXERCISE_SLUG,
            'description': (
                'Remember the word by association on time or in free mode, '
                'or choose the correct word association.'
            ),
            'available': False,
            'constraint_description': 'Only words with images.',
            'hints_available': [],
        },
    }
    HINTS_INFO = {
        'show_association': {
            'name': 'Показать ассоциацию',
            'description': 'Показывает случайную ассоциацию этого слова',
        },
        'show_first_letter': {
            'name': 'Показать первую букву',
            'description': 'Показывает первую букву случайного перевода этого слова',
        },
        'show_letters_amount': {
            'name': 'Показать количество букв',
            'description': 'Показывает количество букв случайного перевода этого слова',
        },
        'show_synonym': {
            'name': 'Показать синоним',
            'description': 'Показывает случайный синоним этого слова',
        },
        'remove_incorrect': {
            'name': 'Убрать вариант',
            'description': 'Показывает один неправильный вариант ответа из предложенных',
        },
    }

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        cnt = 0
        for code, data in tqdm(
            self.HINTS_INFO.items(), desc='Importing exercises hints'
        ):
            try:
                hint, created = Hint.objects.get_or_create(code=code, **data)
                if created:
                    cnt += 1
            except Exception as e:
                raise CommandError('Error adding hint %s: %s' % (hint, e))
        self.stdout.write('Added %d exercises hints' % cnt)
        cnt = 0
        for code, data in tqdm(self.EXERCISES_INFO.items(), desc='Importing exercises'):
            try:
                hints_available = data.pop('hints_available')
                exercise, created = Exercise.objects.get_or_create(**data)
                try:
                    icon_url = self.icons_path + code + '.svg'
                    exercise_icon = ImageFile(open(icon_url, 'rb'))
                    exercise.icon = exercise_icon
                    exercise.save()
                except FileNotFoundError:
                    pass
                if created:
                    cnt += 1
                if exercise.available:
                    for hint_code in hints_available:
                        exercise.hints_available.add(Hint.objects.get(code=hint_code))
            except Exception as e:
                self.stdout.write(f'Error adding exercise {e}')
        self.stdout.write('Added %d exercises' % cnt)

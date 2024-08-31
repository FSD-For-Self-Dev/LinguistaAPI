"""Custom command to delete all media files."""

import os

from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    """Command to delete all media files."""

    help = 'This command deletes all media files from the MEDIA_ROOT directory.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--root',
            nargs='?',
            type=str,
            default='',
            help='Pass if you want to clean only certain dir',
        )

    def handle(self, *args, **options):
        # Get all files from the MEDIA_ROOT, recursively
        media_root = getattr(settings, 'MEDIA_ROOT', None)
        if media_root is not None:
            main_root = os.path.join(media_root, options['root'])

            for relative_root, dirs, files in os.walk(main_root):
                for file_ in files:
                    # Delete file
                    # print(relative_root, dirs)
                    os.remove(os.path.join(relative_root, file_))

            # Bottom-up - delete all empty folders
            for relative_root, dirs, files in os.walk(main_root, topdown=False):
                for dir_ in dirs:
                    if not os.listdir(os.path.join(relative_root, dir_)):
                        os.rmdir(os.path.join(relative_root, dir_))

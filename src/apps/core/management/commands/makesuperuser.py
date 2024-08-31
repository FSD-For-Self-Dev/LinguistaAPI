""" Custom command for quick admin creation """

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string

from dotenv import load_dotenv

from apps.core.signals import admin_created

load_dotenv()

User = get_user_model()


class Command(BaseCommand):
    """
    Command to create admin
    """

    def handle(self, *args, **options):
        username = 'admin'
        email = 'admin@example.com'
        try:
            if (
                not User.objects.filter(username=username).exists()
                and not User.objects.filter(is_superuser=True).exists()
            ):
                self.stdout.write('Admin user not found, creating one')

                new_password = os.getenv(
                    'DJANGO_SUPERUSER_PASSWORD', default=get_random_string(10)
                )

                superuser = User.objects.create_superuser(username, email, new_password)

                self.stdout.write('===================================')
                self.stdout.write(
                    f"A superuser '{username}' was created with email "
                    f"'{email}' and password '{new_password}'"
                )
                self.stdout.write('===================================')

                admin_created.send(sender=User, instance=superuser)
            else:
                self.stdout.write('Admin user found. Skipping super user creation')
        except Exception as e:
            self.stdout.write(f'Error adding superuser : {e}')

import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Create or update the requested admin account from environment variables.'

    def handle(self, *args, **options):
        User = get_user_model()
        username = os.getenv('ADMIN_USERNAME', 'Admin111')
        email = os.getenv('ADMIN_EMAIL', 'admin111@gmail.com')
        password = os.getenv('ADMIN_PASSWORD', 'Admin1234')
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            user.email = email
            user.is_superuser = True
            user.is_staff = True
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Updated admin {username}'))
        else:
            user = User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f'Created admin {username}'))

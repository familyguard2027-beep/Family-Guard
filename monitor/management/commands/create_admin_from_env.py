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
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': email, 'is_staff': True, 'is_superuser': True},
        )
        user.email = email
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        user.set_password(password)
        user.save()

        User.objects.exclude(pk=user.pk).filter(is_superuser=True).update(
            is_active=False,
            is_staff=False,
            is_superuser=False,
        )

        action = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(f'{action} admin {username}'))

from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from rest_framework_simplejwt.tokens import RefreshToken


class Command(BaseCommand):
    """
    Django Management Command to provision a read-only service account
    for machine-to-machine consumers (e.g. the FactoryPulse MCP server /
    AI assistant) and print a long-lived JWT access token for it.

    Usage: python manage.py create_service_token [--username NAME] [--days N]

    The account has no password (set_unusable_password), is not staff and
    is not a superuser, so it can only do what an authenticated regular user
    can do against the read-only analytics endpoints. Copy the printed token
    into the consumer's environment (e.g. FACTORYPULSE_TOKEN) — never commit it.
    """
    help = 'Creates (or reuses) a read-only service account and prints a long-lived JWT access token for it.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username', default='ai-service-readonly',
            help="Username for the service account (default: ai-service-readonly).",
        )
        parser.add_argument(
            '--days', type=int, default=365,
            help="Access token lifetime in days (default: 365).",
        )

    def handle(self, *args, **options):
        username = options['username']
        days = options['days']

        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': f'{username}@factorypulse.local'},
        )
        if created:
            user.set_unusable_password()
            user.is_staff = False
            user.is_superuser = False
            user.save()
            self.stdout.write(self.style.SUCCESS(
                f"Created read-only service account '{username}' (no password, no staff/admin rights)."
            ))
        else:
            self.stdout.write(f"Reusing existing service account '{username}'.")

        access_token = RefreshToken.for_user(user).access_token
        access_token.set_exp(lifetime=timedelta(days=days))

        self.stdout.write(self.style.SUCCESS(
            f"\nService token (valid for {days} days) — set this as FACTORYPULSE_TOKEN:\n"
        ))
        self.stdout.write(str(access_token))
        self.stdout.write("")

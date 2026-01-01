from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Create default admin user if not exists'

    def handle(self, *args, **options):
        username = 'hepham'
        password = 'Phamvanhe07@'
        
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'User "{username}" already exists'))
            return
        
        User.objects.create_superuser(
            username=username,
            email='hepham@admin.local',
            password=password
        )
        self.stdout.write(self.style.SUCCESS(f'Created superuser "{username}"'))

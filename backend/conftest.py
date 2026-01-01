import os
import django
from django.conf import settings

def pytest_configure():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    
    if not settings.configured:
        settings.DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        }
    
    django.setup()

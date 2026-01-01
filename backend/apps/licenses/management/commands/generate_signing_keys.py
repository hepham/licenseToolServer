"""
Management command to generate RSA signing key pair for response signing.
"""
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend


class Command(BaseCommand):
    help = 'Generate RSA key pair for signing license server responses'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Overwrite existing keys',
        )
        parser.add_argument(
            '--key-size',
            type=int,
            default=2048,
            help='RSA key size in bits (default: 2048)',
        )

    def handle(self, *args, **options):
        keys_dir = settings.BASE_DIR / 'keys'
        private_key_path = keys_dir / 'private_key.pem'
        public_key_path = keys_dir / 'public_key.pem'

        if not options['force'] and private_key_path.exists():
            self.stdout.write(
                self.style.WARNING(
                    f'Keys already exist at {keys_dir}. Use --force to overwrite.'
                )
            )
            return

        keys_dir.mkdir(exist_ok=True)

        self.stdout.write('Generating RSA key pair...')

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=options['key_size'],
            backend=default_backend()
        )

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        with open(private_key_path, 'wb') as f:
            f.write(private_pem)
        os.chmod(private_key_path, 0o600)

        with open(public_key_path, 'wb') as f:
            f.write(public_pem)

        self.stdout.write(self.style.SUCCESS(f'Private key saved to: {private_key_path}'))
        self.stdout.write(self.style.SUCCESS(f'Public key saved to: {public_key_path}'))
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('IMPORTANT:'))
        self.stdout.write('1. Keep private_key.pem SECRET - never commit to git!')
        self.stdout.write('2. Copy public_key.pem to your SDK distribution')
        self.stdout.write('3. Add LICENSE_SIGNING_KEY to your .env file:')
        self.stdout.write(f'   LICENSE_SIGNING_KEY={private_key_path}')

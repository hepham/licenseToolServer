import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from apps.licenses.models import License, Device
from apps.licenses.utils import generate_device_id, hash_fingerprint, sign_response

try:
    lic = License.objects.filter(status='inactive').first()
    if not lic:
        print('No inactive license found')
        sys.exit(0)
    print('License:', lic.key, 'Status:', lic.status)

    device_id = generate_device_id('cpu-test3', 'disk-test3', 'mb-test3')
    print('Device ID:', device_id)

    fingerprint_data = 'cpu-test3:disk-test3:mb-test3'
    fingerprint_hash = hash_fingerprint(fingerprint_data)
    mac_hash = hash_fingerprint('00:00:00:00:00:03')

    device = Device.objects.create(
        license=lic,
        device_id=device_id,
        fingerprint_hash=fingerprint_hash,
        mac_address_hash=mac_hash
    )
    print('Device created:', device.id)

    lic.status = 'active'
    lic.save()
    print('License activated')

    response = sign_response({
        'success': True,
        'message': 'Test',
        'license_key': lic.key,
        'device_id': device_id
    })
    print('Signed response:', response)
except Exception as e:
    import traceback
    traceback.print_exc()

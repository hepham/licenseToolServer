"""
Signature Verification

Verifies server response signatures to prevent response tampering.
"""

import json
import base64
import time
from typing import Optional

try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.backends import default_backend
    from cryptography.exceptions import InvalidSignature
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False


DEFAULT_PUBLIC_KEY = None

MAX_TIMESTAMP_AGE = 300


class SignatureVerifier:
    """
    Verifies server response signatures using RSA public key.
    
    If no public key is provided, signature verification is skipped.
    """

    def __init__(self, public_key_pem: Optional[str] = None):
        """
        Initialize the signature verifier.
        
        Args:
            public_key_pem: PEM-encoded RSA public key string.
                           If None, verification is disabled.
        """
        self._public_key = None
        
        if public_key_pem and HAS_CRYPTOGRAPHY:
            try:
                self._public_key = serialization.load_pem_public_key(
                    public_key_pem.encode('utf-8'),
                    backend=default_backend()
                )
            except Exception:
                pass

    @property
    def is_enabled(self) -> bool:
        """Check if signature verification is enabled."""
        return self._public_key is not None

    def verify(self, response: dict) -> bool:
        """
        Verify the signature of a server response.
        
        Args:
            response: The response dictionary from the server.
        
        Returns:
            True if signature is valid or verification is disabled.
            False if signature is invalid or missing when verification is enabled.
        """
        if not self.is_enabled:
            return True

        signature_b64 = response.get('signature')
        timestamp = response.get('timestamp')

        if not signature_b64 or timestamp is None:
            return False

        current_time = int(time.time())
        if abs(current_time - timestamp) > MAX_TIMESTAMP_AGE:
            return False

        data_to_verify = {k: v for k, v in response.items() if k != 'signature'}
        payload = json.dumps(data_to_verify, sort_keys=True, separators=(',', ':')).encode('utf-8')

        try:
            signature = base64.b64decode(signature_b64)
            self._public_key.verify(
                signature,
                payload,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            return True
        except (InvalidSignature, Exception):
            return False

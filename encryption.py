"""
AES Encryption Module for Real-Time Communication System
Provides end-to-end encryption for messages, files, and voice data
"""
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
import base64
import hashlib


class AESCipher:
    """AES encryption/decryption with CBC mode"""
    
    def __init__(self, key=None):
        """
        Initialize AES cipher with a key
        If no key provided, generates a random 256-bit key
        """
        if key is None:
            self.key = get_random_bytes(32)  # 256-bit key
        elif isinstance(key, str):
            # Derive key from string using SHA-256
            self.key = hashlib.sha256(key.encode()).digest()
        else:
            self.key = key
    
    def encrypt(self, plaintext):
        """
        Encrypt plaintext using AES-256-CBC
        Returns: base64 encoded string (IV + ciphertext)
        """
        if isinstance(plaintext, str):
            plaintext = plaintext.encode('utf-8')
        
        # Generate random IV
        iv = get_random_bytes(16)
        
        # Create cipher
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        
        # Pad and encrypt
        padded_data = pad(plaintext, AES.block_size)
        ciphertext = cipher.encrypt(padded_data)
        
        # Combine IV + ciphertext and encode
        encrypted_data = iv + ciphertext
        return base64.b64encode(encrypted_data).decode('utf-8')
    
    def decrypt(self, encrypted_data):
        """
        Decrypt AES-256-CBC encrypted data
        Input: base64 encoded string (IV + ciphertext)
        Returns: decrypted plaintext as string
        """
        try:
            # Decode from base64
            encrypted_data = base64.b64decode(encrypted_data)
            
            # Extract IV and ciphertext
            iv = encrypted_data[:16]
            ciphertext = encrypted_data[16:]
            
            # Create cipher and decrypt
            cipher = AES.new(self.key, AES.MODE_CBC, iv)
            padded_plaintext = cipher.decrypt(ciphertext)
            
            # Unpad and return
            plaintext = unpad(padded_plaintext, AES.block_size)
            return plaintext.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")
    
    def encrypt_bytes(self, data):
        """
        Encrypt binary data (for files and voice)
        Returns: bytes (IV + ciphertext)
        """
        # Generate random IV
        iv = get_random_bytes(16)
        
        # Create cipher
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        
        # Pad and encrypt
        padded_data = pad(data, AES.block_size)
        ciphertext = cipher.encrypt(padded_data)
        
        # Return IV + ciphertext
        return iv + ciphertext
    
    def decrypt_bytes(self, encrypted_data):
        """
        Decrypt binary data (for files and voice)
        Input: bytes (IV + ciphertext)
        Returns: decrypted bytes
        """
        try:
            # Extract IV and ciphertext
            iv = encrypted_data[:16]
            ciphertext = encrypted_data[16:]
            
            # Create cipher and decrypt
            cipher = AES.new(self.key, AES.MODE_CBC, iv)
            padded_plaintext = cipher.decrypt(ciphertext)
            
            # Unpad and return
            plaintext = unpad(padded_plaintext, AES.block_size)
            return plaintext
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")
    
    def get_key_base64(self):
        """Get the encryption key as base64 string for sharing"""
        return base64.b64encode(self.key).decode('utf-8')
    
    @staticmethod
    def from_base64_key(key_b64):
        """Create cipher from base64 encoded key"""
        key = base64.b64decode(key_b64)
        return AESCipher(key)


# Global cipher instance for the application
# In production, each user pair should have their own key
_global_cipher = None

def get_cipher(key=None):
    """Get or create global cipher instance"""
    global _global_cipher
    if _global_cipher is None or key is not None:
        if key:
            _global_cipher = AESCipher(key)
        else:
            # Use a default key (in production, this should be per-session)
            _global_cipher = AESCipher("RealTimeCommunicationSystem2024SecureKey")
    return _global_cipher


def encrypt_message(message):
    """Convenience function to encrypt a text message"""
    cipher = get_cipher()
    return cipher.encrypt(message)


def decrypt_message(encrypted_message):
    """Convenience function to decrypt a text message"""
    cipher = get_cipher()
    return cipher.decrypt(encrypted_message)


def encrypt_file_chunk(chunk):
    """Encrypt a file chunk"""
    cipher = get_cipher()
    return cipher.encrypt_bytes(chunk)


def decrypt_file_chunk(encrypted_chunk):
    """Decrypt a file chunk"""
    cipher = get_cipher()
    return cipher.decrypt_bytes(encrypted_chunk)

from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv

load_dotenv()

_encryption_key = os.environ.get('SECRET_CRYPTO_KEY')

if not _encryption_key:
    print('Warning: SECRET_CRYPTO_KEY not set, generating for you')
    _encryption_key = Fernet.generate_key().decode()
    print(f'Generated Dev Key (SET THIS AS CHAT_CRPYTO_KEY): {_encryption_key}')


cypher_suite=Fernet(_encryption_key.encode())


def encrypt_message(plaintext):
    if not plaintext:
        return None
    return cypher_suite.encrypt(plaintext.encode('UTF-8')).decode('UTF-8')


def decrypt_message(cyphertext):
    if not cyphertext:
        return None
    try:
        return cypher_suite.decrypt(cyphertext.encode('UTF-8')).decode('UTF-8')
    except Exception as e:
        print(f'Decryption failed for {e}')
        return '[Decryption Failed]'


""" Auth service functions """
from datetime import datetime, timedelta
import secrets

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password):
    """returns hashed password"""
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    """returns True if password is correct, False if not"""
    return pwd_context.verify(plain_password, hashed_password)


def generate_session_token():
    return secrets.token_hex(16)


def generate_session_expiry():
    return datetime.now() + timedelta(days=3)

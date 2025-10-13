""" Auth service functions """
import re

from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password):
    """returns hashed password"""
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    """returns True if password is correct, False if not"""
    return pwd_context.verify(plain_password, hashed_password)

def is_valid_email(email: str) -> bool:
        # Define the regular expression for validating an email
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

        # Use the re.match() function to check if the email matches the pattern
        return re.match(email_regex, email) is not None

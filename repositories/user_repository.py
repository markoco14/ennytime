"""CRUD functions for users table"""

from memory_db import USERS
from schemas import User


def list_users():
    """ Returns a list of users """
    return list(USERS.values())

def patch_user(current_user: User, display_name: str = None):
    """ Updates a user """
    if display_name is not None:
        current_user.display_name = display_name

    USERS.update({current_user.email: current_user})
    
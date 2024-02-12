"""CRUD functions for users table"""

from memory_db import USERS


def list_users():
    """ Returns a list of users """
    return list(USERS.values())

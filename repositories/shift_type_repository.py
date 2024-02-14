"""
Functions for retrieving data from any table in the database
"""

from core.memory_db import SHIFT_TYPES


def list_user_shift_types(user_id: int):
	""" Returns a list of shift types for a given user """
	shift_types = [shift_type for shift_type in list(SHIFT_TYPES.values()) if shift_type.user_id == user_id]
	
	return shift_types

def get_shift_type(shift_type_id: int):
	""" Returns a shift type for a given shift type id """
	shift_type = SHIFT_TYPES.get(shift_type_id)
	
	return shift_type


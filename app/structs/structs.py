from collections import namedtuple


ShiftRow = namedtuple("ShiftRow", ("id", "long_name", "short_name"))

ShiftCreate = namedtuple("ShiftCreate", ("long_name", "short_name", "user_id"))
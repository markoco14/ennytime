from collections import namedtuple


UserRow = namedtuple("UserRow", ("id", "display_name", "is_admin", "birthday", "username"))

ShiftRow = namedtuple("ShiftRow", ("id", "long_name", "short_name"))
ShiftCreate = namedtuple("ShiftCreate", ("long_name", "short_name", "user_id"))
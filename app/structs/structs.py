from collections import namedtuple


UserRow = namedtuple("UserRow", ("id", "display_name", "is_admin", "birthday", "username", "email"))
UserLoginRow = namedtuple("UserLoginRow", ("id", "display_name", "is_admin", "birthday", "username", "email", "hashed_password"))

ShiftRow = namedtuple("ShiftRow", ("id", "long_name", "short_name"))
ShiftCreate = namedtuple("ShiftCreate", ("long_name", "short_name", "user_id"))

ScheduleRow = namedtuple("ScheduleRow", ("id", "shift_id", "user_id", "date"))
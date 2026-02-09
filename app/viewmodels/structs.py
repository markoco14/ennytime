from collections import namedtuple


ShiftCreate = namedtuple("ShiftCreate", ("long_name", "short_name", "user_id"))

ScheduleRow = namedtuple("ScheduleRow", ("id", "shift_id", "user_id", "date"))
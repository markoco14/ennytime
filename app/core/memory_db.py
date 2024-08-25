"""
In-memory database for the application.
This is a temporary solution.
"""

import datetime
from app.schemas import schemas


# SHIFT_TYPES: dict[ShiftType] = {
# 	1: ShiftType(
# 		id=1,
# 		type="D",
# 		user_id=2,
# 	),
# 	2: ShiftType(
# 		id=2,
# 		type="N",
# 		user_id=3,
# 	),
# 	3: ShiftType(
# 		id=3,
# 		type="W",
# 		user_id=3,
# 	),
# 	4: ShiftType(
# 		id=4,
# 		type="W",
# 		user_id=4,
# 	),
# }


# SHIFTS: list[Shift] = [
# 	Shift(
# 		id=1,
# 		type_id=2,
# 		user_id=3,
# 		date=datetime.datetime(2024, 2, 9),
# 		type=SHIFT_TYPES[2],
# 	),
# 	Shift(
# 		id=2,
# 		type_id=3,
# 		user_id=3,
# 		date=datetime.datetime(2024, 2, 11),
# 		type=SHIFT_TYPES[3],
# 	),
# 	Shift(
# 		id=3,
# 		type_id=1,
# 		user_id=2,
# 		date=datetime.datetime(2024, 2, 11),
# 		type=SHIFT_TYPES[1],
# 	),
# 	Shift(
# 		id=4,
# 		type_id=2,
# 		user_id=3,
# 		date=datetime.datetime(2024, 2, 19),
# 		type=SHIFT_TYPES[2],
# 	),
# 	Shift(
# 		id=5,
# 		type_id=2,
# 		user_id=1,
# 		date=datetime.datetime(2024, 2, 19),
# 		type=SHIFT_TYPES[2],
# 	),
# 	Shift(
# 		id=6,
# 		type_id=3,
# 		user_id=2,
# 		date=datetime.datetime(2024, 2, 19),
# 		type=SHIFT_TYPES[3],
# 	),
# ]


SHARES: dict[schemas.Share] = {
}
# "owner2guest3": Share(
# 	id=1,
# 	sender_id=2,
# 	guest_id=3,
# ),
# "owner1guest2": Share(
# 	id=2,
# 	sender_id=1,
# 	guest_id=2,
# ),
# "owner3guest4": Share(
# 	id=3,
# 	sender_id=3,
# 	guest_id=4,
# )


# SESSIONS: dict[Session]= {
# 	"first-test-session": Session(
# 		id=1,
# 		session_id="a-test-session",
# 		user_id=1,
# 		expires_at="2024-02-14 23:59:59"
# 	),
# 	"second-test-session": Session(
# 		id=2,
# 		session_id="a-test-session",
# 		user_id=2,
# 		expires_at="2024-02-09 23:59:59"
# 	),
# }


USERS: dict[schemas.User] = {
    "johndoe@example.com": schemas.User(
        id=1,
        email="johndoe@example.com",
        password="fakehashedsecret"
    ),
    "alice@example.com": schemas.User(
        id=2,
        email="alice@example.com",
        password="fakehashedsecret"
    ),
    "mark.oconnor14@gmail.com": schemas.User(
        id=3,
        email="mark.oconnor14@gmail.com",
        password="$2b$12$.hJ1LOqpdFZldlwiSnDUUeorgtwjIB68u0tTZwD2kjPNjRIP0.tPK",
        display_name="Mark O'Connor"
    ),
    "rose@rosemail.com": schemas.User(
        id=4,
        email="rose@rosemail.com",
        password="$2b$12$.hJ1LOqpdFZldlwiSnDUUeorgtwjIB68u0tTZwD2kjPNjRIP0.tPK",
        display_name="Rose Rosie"
    ),
}

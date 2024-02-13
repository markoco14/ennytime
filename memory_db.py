"""
In-memory database for the application.
This is a temporary solution.
"""

import datetime
from schemas import Session, Shift, ShiftType, User




SHIFT_TYPES: dict[ShiftType] = {
	1: ShiftType(
		id=1,
		type="D",
		user_id=2,
	),
	2: ShiftType(
		id=2,
		type="N",
		user_id=3,
	),
	3: ShiftType(
		id=3,
		type="W",
		user_id=3,
	),
	4: ShiftType(
		id=4,
		type="W",
		user_id=4,
	),
}


SHIFTS: list[Shift] = [
	Shift(
		id=1,
		type_id=2,
		user_id=3,
		date=datetime.datetime(2024, 2, 9),
		type=SHIFT_TYPES[2],
	),
]




SESSIONS: dict[Session]= {
	"first-test-session": Session(
		id=1,
		session_id="a-test-session",
		user_id=1,
		expires_at="2024-02-14 00:00:00"
	),
	"second-test-session": Session(
		id=2,
		session_id="a-test-session",
		user_id=2,
		expires_at="2024-02-09 00:00:00"
	),
	"9d5fb05379ea64e7aaf2756d7048bfab": Session(
		id=3,
		session_id="9d5fb05379ea64e7aaf2756d7048bfab",
		user_id=3,
		expires_at="2024-02-12 23:59:59"
	),
}


USERS: dict[User] = {
    "johndoe@example.com": User(
		id=1,
        email="johndoe@example.com",
        password="fakehashedsecret"
        ),
    "alice@example.com": User(
		id=2,
        email="alice@example.com",
        password="fakehashedsecret"
        ),
    "mark.oconnor14@gmail.com": User(
		id=3,
        email="mark.oconnor14@gmail.com",
        password="$2b$12$.hJ1LOqpdFZldlwiSnDUUeorgtwjIB68u0tTZwD2kjPNjRIP0.tPK"
        ),
}

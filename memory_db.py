"""
In-memory database for the application.
This is a temporary solution.
"""

from schemas import Session, ShiftType, User




SHIFT_TYPES: list[ShiftType] = [
	ShiftType(
		id=1,
		type="D",
		user_id=2,
	),
	ShiftType(
		id=2,
		type="N",
		user_id=3,
	),
	ShiftType(
		id=3,
		type="W",
		user_id=3,
	),
	ShiftType(
		id=4,
		type="W",
		user_id=4,
	),
]


SHIFTS = []


USER_ID = 4
SESSION_ID = 4


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
	"58ce46c62a116760ef76cb2b791d310e": Session(
		id=3,
		session_id="58ce46c62a116760ef76cb2b791d310e",
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

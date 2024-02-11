"""
In-memory database for the application.
This is a temporary solution.
"""

import calendar_service
from schemas import Session, User


DAYS_OF_WEEK = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]


SHIFT_TYPES = ["W", "D", "N"]


SHIFTS = []


MONTH_CALENDAR = calendar_service.get_month_calendar(2024, 2)


USER_ID = 4


SESSIONS: dict[Session]= {
	"first-test-session": Session(
		session_id="a-test-session",
		user_id=1,
		expires_at="2024-02-14 00:00:00"
	),
	"second-test-session": Session(
		session_id="a-test-session",
		user_id=2,
		expires_at="2024-02-09 00:00:00"
	)
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

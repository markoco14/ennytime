import calendar

month_calendar = calendar.Calendar(firstweekday=6)

def get_month_calendar(year, month):
	return month_calendar.monthdayscalendar(year, month)



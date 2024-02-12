"""Functions for calendar"""

import calendar
import datetime

DAYS_OF_WEEK = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

MONTH_CALENDAR = calendar.Calendar(firstweekday=6)

def get_current_month(month):
    """ Returns the current month or the user's selected month"""
    if not month:
        current_month = datetime.date.today().month
    else:
        current_month = month

    return current_month

def get_current_year(year):
    """ Returns the current year or the user's selected year"""
    if not year:
        current_year = datetime.date.today().year
    else:
        current_year = year

    return current_year

def get_month_calendar(year, month):
    """ Returns the month calendar for the current month/year
    or the user's selected month/year"""
    return MONTH_CALENDAR.monthdayscalendar(year, month)



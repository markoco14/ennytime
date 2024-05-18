"""Functions for calendar"""

import calendar
import datetime
from enum import Enum

class Weekday(Enum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

    def __str__(self):
        if self.value == 0:
            return "Monday"
        elif self.value == 1:
            return "Tuesday"
        elif self.value == 2:
            return "Wednesday"
        elif self.value == 3:
            return "Thursday"
        elif self.value == 4:
            return "Friday"
        elif self.value == 5:
            return "Saturday"
        elif self.value == 6:
            return "Sunday"
        

DAYS_OF_WEEK = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]

MONTH_CALENDAR = calendar.Calendar(firstweekday=6)


def get_current_day(day):
    if not day:
        current_day = datetime.date.today().day
    else:
        current_day = day

    return current_day


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
    return MONTH_CALENDAR.itermonthdates(year, month)

def get_month_date_list(year, month):
    """Returns a list of dates for the given month/year"""
    return MONTH_CALENDAR.itermonthdays4(year, month)
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


def extract_date_string_numbers(date_string: str):
    """ Returns the year, month, and day from a date string in integer format """
    year = int(date_string.split("-")[0])
    month = int(date_string.split("-")[1])
    day = int(date_string.split("-")[2])

    return year, month, day


def get_prev_and_next_month_names(current_month: int):
    """ Takes the current month and returns the names of the next month and previous month. Corrects for December and January """
    if current_month == 1:
        prev_month_name = MONTHS[11]
    else:
        prev_month_name = MONTHS[current_month - 2]

    if current_month == 12:
        next_month_name = MONTHS[0]
    else:
        next_month_name = MONTHS[current_month]
    
    return prev_month_name, next_month_name


def get_weekday(date):
    """ Returns the day of the week for a given date"""
    day = calendar.weekday(
        int(date.split("-")[0]), int(date.split("-")[1]), int(date.split("-")[2]))

    return Weekday(day)


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


def get_start_of_month(year, month):
    """Returns the first day of the month"""
    return datetime.datetime(year, month, 1)


def get_end_of_month(year, month):
    """Returns the last day of the month"""
    if month == 12:
        return datetime.datetime(year + 1, 1, 1) + datetime.timedelta(seconds=-1)
    else:
        return datetime.datetime(year, month + 1, 1) + datetime.timedelta(seconds=-1)

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel


import time_service

app = FastAPI()

templates = Jinja2Templates(directory="templates")

class ScheduleDay(BaseModel):
	"""Schedule day"""
	date: int
	type: str

DAYS_OF_WEEK = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

SHIFT_TYPES = ["N","D","W"]

SHIFTS = [
	ScheduleDay(date=1, type="N"),
	ScheduleDay(date=11, type="N"),
	ScheduleDay(date=21, type="N"),
	ScheduleDay(date=25, type="N"),
	ScheduleDay(date=29, type="N"),
]

MONTH_CALENDAR = time_service.get_month_calendar(2024, 2)
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
	"""Index page"""

	context = {
		"request": request,
		"days_of_week": DAYS_OF_WEEK,
		"month_calendar": MONTH_CALENDAR,
		"shifts": SHIFTS,
	}

	return templates.TemplateResponse(
		request=request,
		name="index.html",
		context=context
		)

@app.get("/profile", response_class=HTMLResponse)
def profile(request: Request):
	"""Profile page"""

	context = {
		"request": request,
	}

	return templates.TemplateResponse(
		request=request,
		name="profile.html",
		context=context
		)
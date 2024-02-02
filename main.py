from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates



import time_service

app = FastAPI()

templates = Jinja2Templates(directory="templates")

DAYS_OF_WEEK = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

SHIFT_TYPES = ["N","D","W"]

SHIFTS = [
	{
		"type": "N",
		"date": 1
	},
	{
		"type": "N",
		"date": 11
	},
	{
		"type": "D",
		"date": 21
	},
	{
		"type": "N",
		"date": 25
	},
	{
		"type": "W",
		"date": 29
	},
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
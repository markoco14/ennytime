from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()

templates = Jinja2Templates(directory="templates")

DAYS_OF_WEEK = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
	"""Index page"""

	context = {
		"request": request,
		"days_of_week": DAYS_OF_WEEK
	}
	
	return templates.TemplateResponse(
		request=request, 
		name="index.html",
		context=context
		)
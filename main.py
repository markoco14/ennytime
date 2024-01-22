from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def index():
	"""Index page"""
	return {"status": "healthy"}
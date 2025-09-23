from fastapi import FastAPI

# Create an instance of the FastAPI class
app = FastAPI()

# Define a "route" or "endpoint"
@app.get("/")
def read_root():
    return {"message": "Welcome to the ExplainNet API!"}
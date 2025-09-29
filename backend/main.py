
# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess

app = FastAPI()

# ✅ Allow requests from React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CodeRequest(BaseModel):
    code: str

@app.post("/reasoning")
async def reasoning(req: CodeRequest):
    # Simple reasoning placeholder (extend with AI/logic later)
    code = req.code
    reasoning_text = f"Your code has {len(code.splitlines())} lines. It looks like you're using {len(code.split())} tokens."
    return {"reasoning": reasoning_text}

@app.post("/debug")
async def debug(req: CodeRequest):
    try:
        # Run code safely with subprocess (timeout to avoid infinite loops)
        result = subprocess.run(
            ["python", "-c", req.code],
            capture_output=True,
            text=True,
            timeout=5
        )
        output = result.stdout if result.stdout else result.stderr
    except Exception as e:
        output = f"Error: {str(e)}"
    return {"output": output}


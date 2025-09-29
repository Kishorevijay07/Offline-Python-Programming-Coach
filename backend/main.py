import requests
import subprocess
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CodeRequest(BaseModel):
    code: str

@app.post("/reasoning")
async def reasoning(req: CodeRequest):
    try:
        payload = {
            "model": "phi3:mini",
            "prompt": f"Explain this Python code line by line with short and clear explanations within 3 points:{req.code}"
        }

        # Don't use response.json() since Ollama streams multiple objects
        resp = requests.post("http://localhost:11434/api/generate", json=payload, stream=True)

        reasoning_text = ""
        for line in resp.iter_lines():
            if line:
                try:
                    data = line.decode("utf-8")
                    import json
                    obj = json.loads(data)
                    if "response" in obj:
                        reasoning_text += obj["response"]
                except Exception as e:
                    print("Stream parse error:", e)

        return {"reasoning": reasoning_text.strip()}

    except Exception as e:
        return {"reasoning": f"Error fetching reasoning: {str(e)}"}

# --- Debugging with AI explanation ---


OLLAMA_API_URL = "http://localhost:11434/api/generate"
AI_MODEL = "phi3:mini"
@app.post("/debug")
async def debug(req: CodeRequest):
    code = req.code
    if not code.strip():
        return {"output": "No code provided."}

    try:
        # Run code safely
        result = subprocess.run(
            ["python", "-c", code],
            capture_output=True,
            text=True,
            timeout=5
        )
        output = result.stdout.strip() if result.stdout else result.stderr.strip()

        # If error occurs, ask AI to explain
        if result.returncode != 0:
            prompt = f"""
You are an expert Python tutor. The following Python code produced an error.
Explain why the error occurred and give a solution to fix it. return only the explanation and solution, no other text.

Code:
{code}

Error:
{output}

Explain clearly and provide corrected code if possible.
"""

            try:
                res = requests.post(
                    OLLAMA_API_URL,
                    json={
                        "model": AI_MODEL,
                        "prompt": prompt,
                        "max_tokens": 400,
                        "temperature": 0.2
                    },
                    stream=True,
                    timeout=120   # ✅ increase timeout (2 minutes)
                )

                ai_explanation = ""
                for line in res.iter_lines():
                    if line:
                        try:
                            obj = json.loads(line.decode("utf-8"))
                            if "response" in obj:
                                ai_explanation += obj["response"]
                        except Exception as e:
                            print("Stream parse error:", e)

                if ai_explanation.strip():
                    output += "\n\n💡 AI Explanation & Solution:\n" + ai_explanation.strip()
                else:
                    output += "\n\n⚠️ AI did not return any explanation."

            except requests.exceptions.Timeout:
                output += "\n\n⚠️ AI request timed out. Try simplifying the code or increasing timeout further."
            except Exception as e:
                output += f"\n\nError fetching AI explanation: {str(e)}"

    except subprocess.TimeoutExpired:
        output = "Execution timed out (possible infinite loop)."
    except Exception as e:
        output = f"Error during execution: {str(e)}"

    return {"output": output}

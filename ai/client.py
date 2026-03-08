import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "mistral"


def ask_ollama(prompt: str) -> str:
    """
    Sends prompt to local Ollama model and returns response.
    """
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False
        }
    )

    if response.status_code == 200:
        return response.json()["response"]
    else:
        return f"Error: {response.text}"


def tutor_explain(topic: str, context: str = "") -> str:
    prompt = f"""
You are a strict MIT-style tutor.

Explain the topic: {topic}

Context: {context}

Structure:
1. Short explanation
2. Key ideas (bullet points)
3. One worked example
4. 5 test questions at the end
"""
    return ask_ollama(prompt)


def generate_quiz(topic: str, difficulty: str = "medium") -> str:
    prompt = f"""
Create a {difficulty} difficulty quiz on: {topic}

Include:
- 5 conceptual questions
- 3 applied problems
- 2 coding/pseudocode problems
Provide answers at the end.
"""
    return ask_ollama(prompt)

# backend/chatbot.py
import os
import time

# This is a wrapper you can replace with OpenAI/Claude/Gemini API calls.
# For hackathon, we use a simple empathetic reply function. To use real API:
# - set OPENAI_API_KEY env var and implement call_openai_response()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

def generate_reply(user_profile: dict, user_text: str) -> str:
    """
    Simple empathetic fallback. Replace this with API calls.
    Keep replies friendly, empathetic, and academic-assistant aware.
    """
    # quick heuristics
    if any(word in user_text.lower() for word in ["deadline", "assignment", "due", "submit"]):
        return f"I see you're worried about deadlines. Based on your profile, your upcoming assignments: [placeholder]. Want a study plan?"
    if "sad" in user_text.lower() or "depressed" in user_text.lower():
        return "I'm sorry you're feeling this way — I'm here with you. Do you want to tell me more, or see some immediate coping steps?"
    # default
    return "I'm here for you — tell me more so I can help."

# Example for plugging in OpenAI (uncomment and implement)
"""
import openai
def call_openai_response(user_profile, text):
    openai.api_key = OPENAI_API_KEY
    prompt = f\"\"\"You are a supportive, college-focused virtual friend. Student profile: {user_profile}
    Conversation:
    Student: {text}
    Assistant:\"\"\"
    resp = openai.Completion.create(model="gpt-4o-mini", prompt=prompt, max_tokens=200)
    return resp.choices[0].text.strip()
"""

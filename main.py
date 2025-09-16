# main.py  -- Demo FastAPI app for single-click hackathon demo
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import re

app = FastAPI(title="Virtual Friend Demo (Hackathon)")

# --- In-memory stores (demo only) ---
VISIBLE_MEMORY = {}       # email -> list of {text, reply, ts}
PENDING_CASES = []        # list of {id, email, name, score, reason, ts, acknowledged}
CASE_COUNTER = 1

# --- Models ---
class ChatIn(BaseModel):
    email: str
    name: str
    text: str

class ChatOut(BaseModel):
    reply: str

# --- Simple risk config ---
SUICIDAL_PHRASES = [
    "i want to die", "kill myself", "i'm going to kill myself", "end it all",
    "i want to end it", "wish i was dead", "i can't go on", "i can't take it"
]
NEGATIVE_WORDS = ["sad", "depressed", "worthless", "hopeless", "anxious", "stressed", "overwhelmed", "miserable"]
ABSOLUTIST_WORDS = {"always", "never", "nobody", "nothing", "everybody", "completely"}

def contains_suicidal(text: str) -> bool:
    t = text.lower()
    return any(p in t for p in SUICIDAL_PHRASES)

def absolutist_count(text: str) -> int:
    words = re.findall(r"\w+", text.lower())
    return sum(1 for w in words if w in ABSOLUTIST_WORDS)

def neg_ratio(text: str) -> float:
    words = re.findall(r"\w+", text.lower())
    if not words:
        return 0.0
    neg = sum(1 for w in words if w in NEGATIVE_WORDS)
    return neg / len(words)

def compute_risk_score(text: str, behavioral_meta: dict = None) -> (int, str, bool):
    """
    Returns (score int 1-10, reason str, escalate bool)
    """
    suicidal = contains_suicidal(text)
    neg = neg_ratio(text)            # 0..1
    absolutist = absolutist_count(text)
    behaviour = float(behavioral_meta.get("behavior_change", 0.0)) if behavioral_meta else 0.0

    base = 0.4 * neg + 0.25 * (neg) + 0.20 * min(1.0, absolutist / 5.0) + 0.10 * behaviour
    base = max(0.0, min(1.0, base))
    score = 1 + round(base * 9)

    reason = f"base={base:.2f}|neg={neg:.2f}|absol={absolutist}|beh={behaviour:.2f}"
    if suicidal:
        score = max(score, 9)
        escalate = True
        reason += "|suicidal_phrase"
    else:
        escalate = score >= 7

    return int(score), reason, escalate

# --- Simple empathetic reply generator (demo) ---
def generate_reply_simple(name: str, text: str) -> str:
    t = text.lower()
    if any(w in t for w in ["deadline", "assignment", "due", "submit"]):
        return f"Hey {name}, deadlines suck — want a quick study plan? I can help you break it into small steps."
    if any(w in t for w in ["sad", "depressed", "worthless", "hopeless"]):
        return f"I'm sorry you're feeling this way, {name}. I'm here. Do you want to tell me more or see coping steps?"
    return f"Thanks for telling me that, {name}. Tell me more — or ask me about assignments and I can help."

# --- Endpoints ---
@app.get("/")
def root():
    return {"message": "Virtual Friend Demo running. POST /chat to interact."}

@app.post("/chat", response_model=ChatOut)
def chat_endpoint(payload: ChatIn):
    global CASE_COUNTER
    email = payload.email.strip().lower()
    name = payload.name.strip() if payload.name else "Student"
    text = payload.text.strip()

    # store visible memory for student (they can see this)
    mem = VISIBLE_MEMORY.setdefault(email, [])
    # Generate a friendly reply
    reply = generate_reply_simple(name, text)
    mem.append({"text": text, "reply": reply, "ts": datetime.utcnow().isoformat()})

    # compute a simple behavioral meta for demo (here: none)
    history_meta = {"behavior_change": 0.0}

    # risk scoring
    score, reason, escalate = compute_risk_score(text, history_meta)

    # store risk internally only when above low threshold (keeping history)
    if score >= 4:
        PENDING_CASES.append({
            "id": CASE_COUNTER,
            "email": email,
            "name": name,
            "score": score,
            "reason": reason,
            "ts": datetime.utcnow().isoformat(),
            "acknowledged": False
        })
        CASE_COUNTER += 1

    # escalate (notify counsellor) only when escalate True OR suicidal phrase
    if escalate:
        # Notification: in demo we log/print — you can replace with webhook/email/SMS
        notify_payload = {
            "student_email": email,
            "student_name": name,
            "score": score,
            "reason": reason,
            "ts": datetime.utcnow().isoformat()
        }
        # IMPORTANT: do NOT include chat transcripts here. Only minimal student info + score.
        print("=== NOTIFY_COUNSELLOR (DEMO LOG) ===")
        print(notify_payload)
        print("====================================")

    # return only the reply to the student (never the score)
    return {"reply": reply}

@app.get("/memory/{email}")
def view_visible_memory(email: str):
    """Student-visible memory — in demo we return the visible logs to the student."""
    email = email.strip().lower()
    return {"email": email, "visible_memory": VISIBLE_MEMORY.get(email, [])}

@app.get("/counsellor/pending")
def counsellor_pending():
    """Counsellor view for demo: list pending risky cases.
    IMPORTANT: No chat messages here, only student basic info + score + timestamp."""
    # return only minimal info
    return [
        {
            "case_id": c["id"],
            "email": c["email"],
            "name": c["name"],
            "score": c["score"],
            "reason": c["reason"],
            "ts": c["ts"],
            "acknowledged": c["acknowledged"]
        }
        for c in PENDING_CASES if not c["acknowledged"]
    ]

@app.post("/counsellor/ack/{case_id}")
def counsellor_ack(case_id: int):
    for c in PENDING_CASES:
        if c["id"] == case_id:
            c["acknowledged"] = True
            return {"ok": True, "case_id": case_id}
    raise HTTPException(status_code=404, detail="case not found")

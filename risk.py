# backend/risk.py
from typing import Dict
from transformers import pipeline
import re

# Basic transformer models may be heavy in demo; optionally stub with small rule-based
# If you have GPU and transformers installed, uncomment pipelines. For hackathon small CPU demo,
# fallback to rule-based functions.

try:
    sentiment_pipe = pipeline("sentiment-analysis")
    emotion_pipe = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base", return_all_scores=True)
    HAS_PIPELINES = True
except Exception as e:
    print("Could not initialize transformers pipelines (will use rule heuristics):", e)
    sentiment_pipe = None
    emotion_pipe = None
    HAS_PIPELINES = False

SUICIDAL_PHRASES = [
    "i want to die", "i'm going to kill myself", "end it all", "i can't go on",
    "i want to end it", "i wish i was dead", "kill myself"
]

ABSOLUTIST_WORDS = {"always", "never", "nobody", "nothing", "everybody", "completely"}

def _contains_suicidal(text: str) -> bool:
    t = text.lower()
    return any(ph in t for ph in SUICIDAL_PHRASES)

def _absolutist_count(text: str) -> int:
    words = re.findall(r"\w+", text.lower())
    return sum(1 for w in words if w in ABSOLUTIST_WORDS)

def analyze_text_simple(text: str) -> Dict:
    txt = text.lower()
    suicidal = _contains_suicidal(txt)
    absol = _absolutist_count(txt)
    # naive sentiment
    neg_score = 0.0
    distress = 0.0
    if HAS_PIPELINES and sentiment_pipe:
        try:
            sent = sentiment_pipe(text[:512])[0]
            # label may be POSITIVE/NEGATIVE
            if sent['label'].lower().startswith('negative'):
                neg_score = float(sent['score'])
            else:
                neg_score = 1.0 - float(sent['score'])
        except:
            neg_score = 0.0
    else:
        # heuristic
        neg_words = ["sad", "depressed", "worthless", "hopeless", "anxious", "stressed", "overwhelmed"]
        neg_score = sum(txt.count(w) for w in neg_words) / max(1, len(txt.split()))
        neg_score = min(1.0, neg_score)
    # distress via emotion pipeline if available
    distress = 0.0
    if HAS_PIPELINES and emotion_pipe:
        try:
            res = emotion_pipe(text[:512])
            for r in res:
                if r['label'].lower() in ['sadness', 'fear', 'anger']:
                    distress += r['score']
            distress = min(1.0, distress)
        except:
            distress = 0.0
    else:
        distress = neg_score * 0.9

    return {"suicidal": suicidal, "neg_score": float(neg_score), "distress": float(distress), "absolutist": int(absol)}

def compute_risk_score(text: str, user_history_meta: dict = None) -> Dict:
    """
    Returns: {'score': int(1-10), 'escalate': bool, 'reason': str}
    """
    meta = analyze_text_simple(text)
    base = 0.0
    base += 0.4 * meta['neg_score']
    base += 0.25 * meta['distress']
    base += 0.20 * min(1.0, meta['absolutist'] / 5.0)
    # We might use user_history_meta for behavioral signals like late-night messages or drop in engagement.
    behavioral = float(user_history_meta.get("behavioral_change", 0.0)) if user_history_meta else 0.0
    base += 0.10 * behavioral
    base = max(0.0, min(1.0, base))
    score = 1 + round(base * 9)
    reason = f"base={base:.2f}|neg={meta['neg_score']:.2f}|distress={meta['distress']:.2f}|absol={meta['absolutist']}"
    if meta['suicidal']:
        score = max(score, 9)
        escalate = True
        reason += "|suicidal_phrase"
    else:
        escalate = score >= 7
    return {"score": int(score), "escalate": escalate, "reason": reason}

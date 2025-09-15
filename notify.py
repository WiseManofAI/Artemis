# backend/notify.py
import logging
logger = logging.getLogger("notify")
logger.setLevel(logging.INFO)

def notify_counsellor(score_obj: dict, user_info: dict):
    """
    For hackathon: log. Replace with email, webhook, SMS or internal dashboard event.
    Only send numeric score + minimal identifying info (name, college, enrollment).
    Do NOT send chat transcripts.
    """
    payload = {
        "student_email": user_info.get("email"),
        "student_name": user_info.get("full_name"),
        "college": user_info.get("college"),
        "enrollment": user_info.get("enrollment"),
        "score": score_obj["score"],
        "reason": score_obj.get("reason")
    }
    logger.info("NOTIFY_COUNSELLOR: %s", payload)
    # For hackathon, we just log. Real: send to secured counsellor webhook or create a DB record.
    return True

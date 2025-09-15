# backend/main.py
from fastapi import FastAPI, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from . import db, models, schemas, auth, chatbot, risk, notify
from .db import engine
from .models import User, ChatMessage, RiskScore, UserMemory, CounselorProfile

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Virtual Friend + Mental Sentinel (Hackathon MVP)")

# simple dependency
def get_db():
    gen = db.SessionLocal()
    try:
        yield gen
    finally:
        gen.close()

@app.post("/register", response_model=dict)
def register(user_in: schemas.UserCreate, db_session: Session = Depends(get_db)):
    # basic user creation; in demo password is saved hashed
    existing = db_session.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = auth.get_password_hash(user_in.password)
    user = User(email=user_in.email, phone=user_in.phone, hashed_password=hashed,
                full_name=user_in.full_name, college=user_in.college, enrollment=user_in.enrollment)
    db_session.add(user)
    db_session.commit()
    return {"ok": True, "email": user.email}

@app.post("/token", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db_session: Session = Depends(get_db)):
    user = db_session.query(User).filter(User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect credentials")
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = auth.create_access_token({"sub": user.email, "role": user.role}, expires_delta=access_token_expires)
    return {"access_token": token, "token_type": "bearer"}

@app.post("/link_portal")
def link_portal(link: dict = Body(...), current_user: User = Depends(auth.get_current_user), db_session: Session = Depends(get_db)):
    """
    Placeholder endpoint where student provides the college portal URL + credentials.
    DO NOT store raw portal credentials in plain text in production. Use OAuth / secure vault.
    """
    portal_url = link.get("portal_url")
    # save placeholder
    current_user.linked_portal = portal_url
    db_session.add(current_user)
    db_session.commit()
    return {"ok": True, "portal_url": portal_url, "note": "Portal integration placeholder - implement college-specific connector."}

@app.post("/chat", response_model=schemas.ChatOut)
def chat(payload: schemas.ChatIn, current_user: User = Depends(auth.get_current_user), db_session: Session = Depends(get_db)):
    # 1) persist chat message
    msg = ChatMessage(user_id=current_user.id, role="user", text=payload.text)
    db_session.add(msg)
    db_session.commit()

    # 2) generate reply
    user_profile = {"email": current_user.email, "college": current_user.college, "enrollment": current_user.enrollment}
    reply_text = chatbot.generate_reply(user_profile, payload.text)

    bot_msg = ChatMessage(user_id=current_user.id, role="bot", text=reply_text)
    db_session.add(bot_msg)
    db_session.commit()

    # 3) risk analyze (synchronous for hackathon - in prod do async/background)
    # compute behavioral meta (very simple: count of messages)
    history_meta = {"behavioral_change": 0.0}
    count_msgs = db_session.query(ChatMessage).filter(ChatMessage.user_id==current_user.id).count()
    if count_msgs >= 10:
        # trivial heuristic for demo: if >10 messages and many late-night (not implemented) -> raise
        history_meta["behavioral_change"] = 0.1

    score_obj = risk.compute_risk_score(payload.text, user_history_meta=history_meta)

    # store risk but only if escalate or above low threshold (we keep history anyway, but mark)
    if score_obj["score"] >= 4:
        rs = RiskScore(user_id=current_user.id, score=score_obj["score"], reason=score_obj.get("reason"))
        db_session.add(rs)
        db_session.commit()

    # escalate to counsellor if required
    if score_obj["escalate"]:
        notify.notify_counsellor(score_obj, user_profile)

    return {"reply": reply_text}

# Counsellor endpoints
@app.get("/counsellor/pending", response_model=list)
def counsellor_pending(current_user: User = Depends(auth.require_role("counsellor")), db_session: Session = Depends(get_db)):
    # return list of recent risky cases (anonymous minimally)
    q = db_session.query(RiskScore).filter(RiskScore.acknowledged==False).order_by(RiskScore.created_at.desc()).all()
    out = []
    for r in q:
        user = db_session.query(User).filter(User.id==r.user_id).first()
        out.append({
            "risk_id": r.id,
            "score": r.score,
            "reason": r.reason,
            "created_at": r.created_at.isoformat(),
            "student_email": user.email,
            "student_name": user.full_name,
            "college": user.college,
            "enrollment": user.enrollment
        })
    return out

@app.post("/counsellor/ack/{risk_id}")
def counsellor_ack(risk_id: int, current_user: User = Depends(auth.require_role("counsellor")), db_session: Session = Depends(get_db)):
    r = db_session.query(RiskScore).filter(RiskScore.id==risk_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Risk not found")
    r.acknowledged = True
    db_session.add(r)
    db_session.commit()
    return {"ok": True}

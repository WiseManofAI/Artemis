# frontend.py -- Streamlit UI for demo chatbot
import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"  # backend FastAPI

st.set_page_config(page_title="Virtual Friend", page_icon="🤖", layout="centered")

if "email" not in st.session_state:
    st.session_state.email = None
if "name" not in st.session_state:
    st.session_state.name = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.title("🤖 Virtual Friend")

# Step 1: Registration
if not st.session_state.email:
    st.subheader("Register")
    with st.form("register_form"):
        name = st.text_input("Your name")
        email = st.text_input("Your email")
        submitted = st.form_submit_button("Start Chatting")
        if submitted:
            if not name or not email:
                st.warning("Please enter both name and email")
            else:
                st.session_state.name = name.strip()
                st.session_state.email = email.strip().lower()
                st.success(f"Welcome, {name}! You can now start chatting.")
                st.experimental_rerun()

# Step 2: Chat UI
else:
    st.subheader(f"Chatting as {st.session_state.name}")
    # load history from backend
    try:
        resp = requests.get(f"{API_URL}/memory/{st.session_state.email}")
        if resp.status_code == 200:
            st.session_state.chat_history = resp.json().get("visible_memory", [])
    except Exception as e:
        st.error("Backend not running. Start FastAPI first.")
    
    # display chat history
    for entry in st.session_state.chat_history:
        with st.chat_message("user"):
            st.write(entry["text"])
        with st.chat_message("assistant"):
            st.write(entry["reply"])
    
    # input box
    if prompt := st.chat_input("Type your message..."):
        payload = {
            "email": st.session_state.email,
            "name": st.session_state.name,
            "text": prompt
        }
        try:
            r = requests.post(f"{API_URL}/chat", json=payload)
            if r.status_code == 200:
                reply = r.json()["reply"]
                # add to local history for instant feedback
                st.session_state.chat_history.append({
                    "text": prompt,
                    "reply": reply
                })
                st.experimental_rerun()
            else:
                st.error("Failed to send message")
        except Exception as e:
            st.error("Backend not reachable. Make sure FastAPI is running.")

# frontend/streamlit_app.py
import streamlit as st
import requests
import os

BACKEND = os.environ.get("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Virtual Friend - Demo", layout="centered")
st.title("Virtual Friend + Mental Sentinel — Demo")

if "token" not in st.session_state:
    st.session_state.token = None
if "role" not in st.session_state:
    st.session_state.role = None
if "email" not in st.session_state:
    st.session_state.email = None

def api_post(path, json=None):
    headers = {}
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    resp = requests.post(BACKEND+path, json=json, headers=headers)
    try:
        return resp.json()
    except:
        return {"error": resp.text}

def api_get(path):
    headers = {}
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    resp = requests.get(BACKEND+path, headers=headers)
    try:
        return resp.json()
    except:
        return {"error": resp.text}

menu = ["Student Sign-up / Login", "Student Chat", "Counsellor Login / Dashboard"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Student Sign-up / Login":
    st.header("Sign-up (Student)")
    with st.form("signup"):
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        full_name = st.text_input("Full name")
        college = st.text_input("College name")
        enrollment = st.text_input("Enrollment no")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Register")
        if submitted:
            payload = {"email": email, "phone": phone, "password": password,
                       "full_name": full_name, "college": college, "enrollment": enrollment}
            r = api_post("/register", json=payload)
            st.write(r)

    st.markdown("---")
    st.header("Login")
    with st.form("login"):
        email = st.text_input("Email for login", key="login_email")
        password = st.text_input("Password for login", type="password", key="login_pw")
        do_login = st.form_submit_button("Login")
        if do_login:
            data = {"username": email, "password": password}
            r = requests.post(BACKEND+"/token", data=data)
            if r.status_code == 200:
                token = r.json()["access_token"]
                st.session_state.token = token
                st.session_state.email = email
                st.success("Logged in!")
            else:
                st.error("Login failed: " + r.text)

    st.markdown("**Portal Linking (placeholder)**")
    st.write("Enter your college portal URL (this is a placeholder for demo).")
    with st.form("link"):
        portal = st.text_input("College portal URL")
        if st.form_submit_button("Link portal"):
            r = api_post("/link_portal", json={"portal_url": portal})
            st.write(r)

elif choice == "Student Chat":
    if not st.session_state.token:
        st.warning("Please login first (Student Login).")
    else:
        st.header("Chat with your virtual friend")
        with st.form("chat"):
            text = st.text_area("Say something", height=120)
            if st.form_submit_button("Send"):
                r = api_post("/chat", json={"text": text})
                if r.get("reply"):
                    st.markdown("**AI:** " + r["reply"])
                else:
                    st.write(r)

        st.markdown("---")
        st.header("Your Visible Memory (student-visible)")
        st.write("This demo does not implement the full memory UI; in prod you would be able to see saved notes & progress here.")

elif choice == "Counsellor Login / Dashboard":
    st.header("Counsellor / Admin Login (Use a counsellor account created via /register and set role to 'counsellor' in DB)")
    with st.form("c_login"):
        email = st.text_input("Counsellor Email", key="c_email")
        password = st.text_input("Counsellor Password", type="password", key="c_pw")
        if st.form_submit_button("Login as counsellor"):
            data = {"username": email, "password": password}
            r = requests.post(BACKEND+"/token", data=data)
            if r.status_code == 200:
                token = r.json()["access_token"]
                st.session_state.token = token
                st.session_state.role = "counsellor"
                st.success("Counsellor logged in.")
            else:
                st.error("Login failed: " + r.text)
    st.markdown("---")
    if st.session_state.role == "counsellor":
        st.subheader("Pending risky cases")
        q = api_get("/counsellor/pending")
        if isinstance(q, dict) and q.get("error"):
            st.write(q)
        else:
            for item in q:
                st.write(item)
                if st.button(f"Acknowledge {item['risk_id']}"):
                    api_post(f"/counsellor/ack/{item['risk_id']}")
                    st.experimental_rerun()

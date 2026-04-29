import streamlit as st
USERS = {
    "admin": {"password": st.secrets["ADMIN_PASSWORD"], "role": "admin"},
    "user": {"password": st.secrets["USER_PASSWORD"], "role": "scientist"},
    "demo": {"password": st.secrets["DEMO_PASSWORD"], "role": "viewer"}
}
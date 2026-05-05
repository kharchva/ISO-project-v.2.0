# import streamlit as st
# import requests
#
# FORMSPREE_URL = "https://formspree.io/f/xbdqkbol"
#
# tab1, tab2, tab3 = st.tabs(["App", "Stats", "Feedback"])
#
# with tab3:
#
#     st.subheader("📩 Feedback / Bug report")
#
#     message = st.text_area("Message *")
#     email = st.text_input("Email (optional)")
#
#     send_btn = st.button("Send feedback")
#
#     if send_btn:
#
#         if not message.strip():
#             st.warning("Message cannot be empty")
#             st.stop()
#
#         data = {
#             "message": message,
#             "email": email
#         }
#
#         response = requests.post(
#             FORMSPREE_URL,
#             data=data
#         )
#
#         # 🔍 діагностика (можеш прибрати потім)
#         # st.write(response.status_code)
#         # st.write(response.text)
#
#         if response.status_code in [200, 201]:
#             st.success("Feedback sent 👍")
#         else:
#             st.error("Failed to send feedback")
#         # st.rerun()


# import streamlit as st
# import requests
# import json
#
# FORMSPREE_URL = "https://formspree.io/f/xbdqkbol"
#
# tab1, tab2 = st.tabs(["Login", "Feedback"])
#
# with tab2:
#
#     st.subheader("📩 Feedback / Bug report")
#
#     message = st.text_area("Message *")
#     email = st.text_input("Email (optional)")
#
#     send_btn = st.button("Send feedback")
#
#     if send_btn:
#
#         if not message.strip():
#             st.warning("Message cannot be empty")
#             st.stop()
#
#         data = {
#             "message": message,
#             "email": email,
#             "role": st.session_state.get("role", "unknown"),
#             "app_state": json.dumps(dict(st.session_state), default=str)[:3000]
#         }
#
#         response = requests.post(
#             FORMSPREE_URL,
#             data=data
#         )
#
#         if response.status_code in [200, 201]:
#             st.success("Feedback sent 👍")
#         else:
#             st.error("Failed to send feedback")

import streamlit as st
import requests
import json

FORMSPREE_URL = "https://formspree.io/f/xbdqkbol"

tab1, tab2 = st.tabs(["Login", "Feedback"])

# 🔥 INIT STATE
if "clear_form" not in st.session_state:
    st.session_state.clear_form = False

if "show_toast" not in st.session_state:
    st.session_state.show_toast = False

if "message" not in st.session_state:
    st.session_state.message = ""

if "email" not in st.session_state:
    st.session_state.email = ""


with tab2:

    st.subheader("📩 Feedback / Bug report")

    # 🔥 RESET FORM (перед рендером полів)
    if st.session_state.clear_form:
        st.session_state.message = ""
        st.session_state.email = ""
        st.session_state.clear_form = False

    # 🔥 TOAST (показується після rerun)
    if st.session_state.show_toast:
        st.toast("Feedback sent 👍", icon="✅")
        st.session_state.show_toast = False

    # 📩 FORM
    message = st.text_area("Message *", key="message")
    email = st.text_input("Email (optional)", key="email")

    send_btn = st.button("Send feedback")

    if send_btn:

        if not message.strip():
            st.warning("Message cannot be empty")
            st.stop()

        data = {
            "message": message,
            "email": email,
            "role": st.session_state.get("role", "unknown"),
            "app_state": json.dumps(dict(st.session_state), default=str)[:3000]
        }

        try:
            response = requests.post(FORMSPREE_URL, data=data)

            if response.status_code in [200, 201]:

                # 🔥 тригери стану
                st.session_state.clear_form = True
                st.session_state.show_toast = True

                # 🔄 rerun
                st.rerun()

            else:
                st.error("Failed to send feedback")

        except Exception as e:
            st.error(f"Error: {e}")
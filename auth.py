import streamlit as st
from database import register_user, login_user

# ─── Admin Credentials ───
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# ─── Check if Logged In ───
def is_logged_in():
    return st.session_state.get('logged_in', False)

# ─── Check if Admin ───
def is_admin():
    return st.session_state.get('is_admin', False)

# ─── Logout ───
def logout():
    st.session_state.logged_in = False
    st.session_state.is_admin = False
    st.session_state.user = None
    st.rerun()

# ─── Login & Register Page ───
def show_auth_page():

    st.markdown("""
        <h1 style='text-align: center; color: #1A365D;'>
            🏠 Kenya House Price Predictor
        </h1>
        <p style='text-align: center; color: #666;'>
            Login or create an account to get started
        </p>
        <hr>
    """, unsafe_allow_html=True)

    # Use radio button instead of tabs
    choice = st.radio(
        "Select Option",
        ["🔐 Login", "📝 Register"],
        horizontal=True
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── Login ───
    if choice == "🔐 Login":
        st.markdown("### Welcome Back!")

        username = st.text_input(
            "Username",
            placeholder="Enter your username",
            key="login_username"
        )
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
            key="login_password"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("🔐 Login", use_container_width=True, key="login_btn"):
            if not username or not password:
                st.error("Please fill in all fields!")

            # Admin login
            elif username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                st.session_state.logged_in = True
                st.session_state.is_admin = True
                st.session_state.user = {'id': 0, 'username': 'Admin'}
                st.success("✅ Welcome Admin!")
                st.rerun()

            # Regular user login
            else:
                success, user, message = login_user(username, password)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.is_admin = False
                    st.session_state.user = user
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

    # ─── Register ───
    elif choice == "📝 Register":
        st.markdown("### Create an Account")

        new_username = st.text_input(
            "Username",
            placeholder="Choose a username",
            key="reg_username"
        )
        new_email = st.text_input(
            "Email",
            placeholder="Enter your email",
            key="reg_email"
        )
        new_password = st.text_input(
            "Password",
            type="password",
            placeholder="Choose a password",
            key="reg_password"
        )
        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            placeholder="Confirm your password",
            key="reg_confirm"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("📝 Create Account", use_container_width=True, key="reg_btn"):
            if not new_username or not new_email or not new_password:
                st.error("Please fill in all fields!")
            elif new_password != confirm_password:
                st.error("❌ Passwords do not match!")
            elif len(new_password) < 6:
                st.error("❌ Password must be at least 6 characters!")
            else:
                success, message = register_user(
                    new_username, new_email, new_password
                )
                if success:
                    st.success(message)
                    st.info("Please select 🔐 Login to sign in!")
                else:
                    st.error(message)
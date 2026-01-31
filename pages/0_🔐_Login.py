"""
🔐 Login & Sign Up Page
Authentication gateway for StudyRAG
"""
import streamlit as st
from supabase import create_client, Client
import os
from dotenv import load_dotenv
import re

load_dotenv()

st.set_page_config(
    page_title="Login - StudyRAG",
    page_icon="🔐",
    layout="centered"
)

# Initialize Supabase client
@st.cache_resource
def get_supabase_client() -> Client:
    """Initialize Supabase client (cached)"""
    return create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_ANON_KEY")
    )

supabase = get_supabase_client()

# Helper functions
def is_valid_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def is_valid_password(password: str) -> tuple[bool, str]:
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"

# Check if already logged in
if st.session_state.get('authenticated'):
    st.success(f"✅ Welcome back, **{st.session_state.get('username', 'User')}**!")
    st.info(f"📧 {st.session_state.get('email')}")
    
    st.markdown("---")
    st.markdown("### 🎯 What would you like to do?")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💬 Go to Chat", use_container_width=True):
            st.switch_page("streamlit_app.py")
    
    with col2:
        if st.button("📚 Upload Textbooks", use_container_width=True):
            st.switch_page("pages/1_📚_Add_Textbooks.py")
    
    st.markdown("---")
    
    if st.button("🚪 Logout", type="secondary"):
        try:
            supabase.auth.sign_out()
        except:
            pass  # Ignore logout errors
        
        # Clear session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        
        st.success("Logged out successfully!")
        st.rerun()
    
    st.stop()

# Not logged in - show login/signup
st.title("🔐 StudyRAG Authentication")
st.markdown("**Your Personal AI Study Assistant**")
st.markdown("Login or create an account to access your textbooks and chat with AI.")

tab1, tab2 = st.tabs(["🔑 Login", "📝 Sign Up"])

# ===== LOGIN TAB =====
with tab1:
    st.markdown("### Login to Your Account")
    
    with st.form("login_form"):
        login_email = st.text_input(
            "Email",
            placeholder="your.email@example.com",
            key="login_email"
        )
        login_password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
            key="login_password"
        )
        
        submit_login = st.form_submit_button("🔓 Login", use_container_width=True, type="primary")
        
        if submit_login:
            # Validation
            if not login_email or not login_password:
                st.error("❌ Please fill in all fields")
            elif not is_valid_email(login_email):
                st.error("❌ Invalid email format")
            else:
                try:
                    with st.spinner("Logging in..."):
                        response = supabase.auth.sign_in_with_password({
                            "email": login_email,
                            "password": login_password
                        })
                    
                    if response.user:
                        # Save to session state
                        st.session_state.authenticated = True
                        st.session_state.user_id = response.user.id
                        st.session_state.email = response.user.email
                        st.session_state.access_token = response.session.access_token
                        st.session_state.refresh_token = response.session.refresh_token
                        
                        # Get username from metadata
                        username = response.user.user_metadata.get('username', 'User')
                        st.session_state.username = username
                        
                        st.success(f"✅ Welcome back, {username}!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Login failed. Please check your credentials.")
                
                except Exception as e:
                    error_msg = str(e)
                    if "Invalid login credentials" in error_msg:
                        st.error("❌ Invalid email or password")
                    elif "Email not confirmed" in error_msg:
                        st.error("❌ Please verify your email first")
                    else:
                        st.error(f"❌ Login failed: {error_msg}")
    
    # Forgot password link
    st.markdown("---")
    with st.expander("🔑 Forgot your password?"):
        reset_email = st.text_input("Enter your email", key="reset_email")
        if st.button("Send Reset Link"):
            if reset_email and is_valid_email(reset_email):
                try:
                    supabase.auth.reset_password_for_email(reset_email)
                    st.success("📧 Password reset link sent! Check your email.")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
            else:
                st.error("❌ Please enter a valid email")

# ===== SIGN UP TAB =====
with tab2:
    st.markdown("### Create New Account")
    
    with st.form("signup_form"):
        signup_email = st.text_input(
            "Email",
            placeholder="your.email@example.com",
            key="signup_email"
        )
        signup_username = st.text_input(
            "Username",
            placeholder="Choose a username (3-50 characters)",
            key="signup_username",
            max_chars=50
        )
        signup_password = st.text_input(
            "Password",
            type="password",
            placeholder="Strong password (min 8 chars, 1 uppercase, 1 number)",
            key="signup_password"
        )
        signup_password_confirm = st.text_input(
            "Confirm Password",
            type="password",
            placeholder="Re-enter your password",
            key="signup_password_confirm"
        )
        
        # Terms acceptance
        accept_terms = st.checkbox(
            "I agree to the Terms of Service and Privacy Policy",
            key="accept_terms"
        )
        
        submit_signup = st.form_submit_button("📝 Create Account", use_container_width=True, type="primary")
        
        if submit_signup:
            # Validation
            if not all([signup_email, signup_username, signup_password, signup_password_confirm]):
                st.error("❌ Please fill in all fields")
            elif not is_valid_email(signup_email):
                st.error("❌ Invalid email format")
            elif len(signup_username) < 3:
                st.error("❌ Username must be at least 3 characters")
            elif ' ' in signup_username:
                st.error("❌ Username cannot contain spaces")
            elif signup_password != signup_password_confirm:
                st.error("❌ Passwords don't match!")
            else:
                # Validate password strength
                is_valid, msg = is_valid_password(signup_password)
                if not is_valid:
                    st.error(f"❌ {msg}")
                elif not accept_terms:
                    st.error("❌ Please accept the Terms of Service")
                else:
                    try:
                        with st.spinner("Creating your account..."):
                            response = supabase.auth.sign_up({
                                "email": signup_email,
                                "password": signup_password,
                                "options": {
                                    "data": {
                                        "username": signup_username
                                    }
                                }
                            })
                        
                        if response.user:
                            st.success("✅ Account created successfully!")
                            
                            # Check if email confirmation is required
                            if response.session:
                                # Auto-logged in (email confirmation disabled)
                                st.session_state.authenticated = True
                                st.session_state.user_id = response.user.id
                                st.session_state.email = response.user.email
                                st.session_state.username = signup_username
                                st.session_state.access_token = response.session.access_token
                                st.session_state.refresh_token = response.session.refresh_token
                                
                                st.balloons()
                                st.success("🎉 You're logged in! Redirecting...")
                                st.rerun()
                            else:
                                # Email confirmation required
                                st.info("📧 Please check your email to verify your account.")
                                st.info("Once verified, you can login using the Login tab.")
                        else:
                            st.error("❌ Signup failed. Please try again.")
                    
                    except Exception as e:
                        error_msg = str(e)
                        if "already registered" in error_msg.lower():
                            st.error("❌ This email is already registered. Please login instead.")
                        elif "weak password" in error_msg.lower():
                            st.error("❌ Password is too weak. Use a stronger password.")
                        else:
                            st.error(f"❌ Signup failed: {error_msg}")
    
    # Password requirements
    with st.expander("ℹ️ Password Requirements"):
        st.markdown("""
        Your password must:
        - Be at least 8 characters long
        - Contain at least one uppercase letter (A-Z)
        - Contain at least one lowercase letter (a-z)
        - Contain at least one number (0-9)
        
        **Example good passwords:**
        - `MyStudy2024!`
        - `SecurePass123`
        - `Learn@NTU2024`
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9em;'>
    <p>🔒 Your data is secured with end-to-end encryption</p>
    <p>StudyRAG • Built with ❤️ for Students</p>
</div>
""", unsafe_allow_html=True)

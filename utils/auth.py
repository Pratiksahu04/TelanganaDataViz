import streamlit as st
import os
import requests

class ReplitAuth:
    def __init__(self):
        self.replit_user_id = os.getenv('REPL_OWNER', None)
        self.replit_user = os.getenv('REPL_OWNER', 'Anonymous')
        
    def get_current_user(self):
        """Get current Replit user information"""
        if self.replit_user_id:
            return {
                'user_id': self.replit_user_id,
                'username': self.replit_user,
                'is_authenticated': True,
                'is_replit_user': True
            }
        else:
            return {
                'user_id': None,
                'username': 'Guest',
                'is_authenticated': False,
                'is_replit_user': False
            }
    
    def is_authenticated(self):
        """Check if user is authenticated via Replit"""
        return self.replit_user_id is not None
    
    def require_auth(self):
        """Require authentication to continue"""
        if not self.is_authenticated():
            st.error("🔒 Authentication Required")
            st.markdown("""
            This application requires Replit authentication to access.
            
            **To use this app:**
            1. Make sure you're logged into Replit
            2. Open this app from your Replit account
            3. Or fork this Repl to your account
            """)
            st.stop()
    
    def show_user_info(self):
        """Display current user information"""
        user = self.get_current_user()
        
        if user['is_authenticated']:
            st.success(f"👋 Welcome, {user['username']}!")
        else:
            st.info("👤 Guest User")
            
        return user
    
    def create_user_session(self):
        """Create or update user session in Streamlit"""
        user = self.get_current_user()
        
        # Store user info in session state
        if 'auth_user' not in st.session_state:
            st.session_state.auth_user = user
        
        return user
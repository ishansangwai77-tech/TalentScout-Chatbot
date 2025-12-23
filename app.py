"""
TalentScout Hiring Assistant - Main Application
A conversational AI chatbot for initial candidate screening.

This module provides the Streamlit frontend interface for the hiring assistant.
"""

import streamlit as st
from dotenv import load_dotenv
import os
from datetime import datetime
from config import APP_TITLE, APP_ICON, COMPANY_NAME, COMPANY_TAGLINE, PRIVACY_NOTICE
from llm_client import LLMClient
from conversation_handler import ConversationHandler
from utils import save_candidate_data

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern, professional styling
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #6366f1;
        --secondary-color: #8b5cf6;
        --accent-color: #06b6d4;
        --bg-dark: #0f172a;
        --bg-card: #1e293b;
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
        --success: #10b981;
        --warning: #f59e0b;
    }
    
    /* Global styles */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
    }
    
    /* Header styling */
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #6366f1, #8b5cf6, #06b6d4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }
    
    .tagline {
        text-align: center;
        color: #94a3b8;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* Chat container */
    .chat-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 1rem;
    }
    
    /* Message bubbles */
    .stChatMessage {
        background: rgba(30, 41, 59, 0.8) !important;
        border-radius: 16px !important;
        border: 1px solid rgba(99, 102, 241, 0.2) !important;
        backdrop-filter: blur(10px);
        margin-bottom: 1rem;
    }
    
    /* User message */
    [data-testid="stChatMessageContent"] {
        color: #f1f5f9 !important;
    }
    
    /* Input field */
    .stChatInputContainer {
        background: rgba(30, 41, 59, 0.9) !important;
        border: 1px solid rgba(99, 102, 241, 0.3) !important;
        border-radius: 12px !important;
    }
    
    .stChatInputContainer input {
        color: #f1f5f9 !important;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%) !important;
        border-right: 1px solid rgba(99, 102, 241, 0.2);
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #f1f5f9;
    }
    
    /* Status card */
    .status-card {
        background: rgba(30, 41, 59, 0.8);
        border-radius: 12px;
        padding: 1rem;
        border: 1px solid rgba(99, 102, 241, 0.2);
        margin-bottom: 1rem;
    }
    
    .status-title {
        color: #06b6d4;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .status-value {
        color: #f1f5f9;
        font-size: 0.9rem;
    }
    
    /* Phase indicator */
    .phase-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    
    .phase-greeting { background: #6366f1; color: white; }
    .phase-info { background: #8b5cf6; color: white; }
    .phase-tech { background: #06b6d4; color: white; }
    .phase-questions { background: #f59e0b; color: white; }
    .phase-conclusion { background: #10b981; color: white; }
    
    /* Button styling */
    .stButton button {
        background: linear-gradient(90deg, #6366f1, #8b5cf6) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1.5rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4) !important;
    }
    
    /* Privacy notice */
    .privacy-notice {
        background: rgba(6, 182, 212, 0.1);
        border: 1px solid rgba(6, 182, 212, 0.3);
        border-radius: 8px;
        padding: 0.75rem;
        font-size: 0.8rem;
        color: #94a3b8;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        color: #64748b;
        font-size: 0.8rem;
        padding: 2rem 0;
        margin-top: 2rem;
    }
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .animate-fade-in {
        animation: fadeIn 0.5s ease-out;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables."""
    if 'llm_client' not in st.session_state:
        try:
            st.session_state.llm_client = LLMClient()
        except ValueError as e:
            st.error(f"⚠️ {str(e)}")
            st.stop()
    
    if 'conversation_handler' not in st.session_state:
        st.session_state.conversation_handler = ConversationHandler(
            st.session_state.llm_client
        )
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'initialized' not in st.session_state:
        st.session_state.initialized = False
    
    if 'conversation_ended' not in st.session_state:
        st.session_state.conversation_ended = False


def get_phase_badge(phase: str) -> str:
    """Get HTML badge for current phase."""
    phase_classes = {
        'greeting': 'phase-greeting',
        'info_gathering': 'phase-info',
        'tech_stack': 'phase-tech',
        'technical_questions': 'phase-questions',
        'conclusion': 'phase-conclusion',
        'ended': 'phase-conclusion'
    }
    phase_labels = {
        'greeting': '👋 Greeting',
        'info_gathering': '📝 Info Gathering',
        'tech_stack': '💻 Tech Stack',
        'technical_questions': '❓ Technical Questions',
        'conclusion': '✅ Conclusion',
        'ended': '🎉 Completed'
    }
    css_class = phase_classes.get(phase, 'phase-greeting')
    label = phase_labels.get(phase, phase.title())
    return f'<span class="phase-badge {css_class}">{label}</span>'


def render_sidebar():
    """Render the sidebar with conversation status and controls."""
    with st.sidebar:
        st.markdown(f"## {APP_ICON} {COMPANY_NAME}")
        st.markdown(f"*{COMPANY_TAGLINE}*")
        st.divider()
        
        # Conversation Status
        st.markdown("### 📊 Conversation Status")
        
        handler = st.session_state.conversation_handler
        phase = handler.get_current_phase()
        
        st.markdown(get_phase_badge(phase), unsafe_allow_html=True)
        
        # Collected Information
        st.markdown("### 📋 Collected Info")
        info = handler.get_candidate_info()
        
        if info:
            for field, value in info.items():
                if value:
                    field_name = field.replace('_', ' ').title()
                    # Truncate long values
                    display_value = value[:30] + "..." if len(value) > 30 else value
                    st.markdown(f"**{field_name}:** {display_value}")
        else:
            st.markdown("*No information collected yet*")
        
        st.divider()
        
        # Privacy Notice
        st.markdown(PRIVACY_NOTICE)
        
        st.divider()
        
        # Controls
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 New Chat", use_container_width=True):
                reset_conversation()
                st.rerun()
        
        with col2:
            if st.button("💾 Export", use_container_width=True):
                export_conversation()
        
        # Footer
        st.markdown(
            f'<div class="footer">© 2024 {COMPANY_NAME}<br>All rights reserved</div>',
            unsafe_allow_html=True
        )


def reset_conversation():
    """Reset the conversation to start fresh."""
    st.session_state.conversation_handler.reset()
    st.session_state.messages = []
    st.session_state.initialized = False
    st.session_state.conversation_ended = False


def export_conversation():
    """Export conversation data to JSON."""
    handler = st.session_state.conversation_handler
    info = handler.get_candidate_info()
    history = handler.get_conversation_history()
    
    if info:
        filepath = save_candidate_data(info, history)
        st.sidebar.success(f"✅ Saved to {filepath}")
    else:
        st.sidebar.warning("No data to export yet")


def render_chat_interface():
    """Render the main chat interface with welcome screen."""
    # Header
    st.markdown(f'<h1 class="main-header">{APP_TITLE}</h1>', unsafe_allow_html=True)
    st.markdown(
        f'<p class="tagline">{COMPANY_TAGLINE} - Powered by AI</p>',
        unsafe_allow_html=True
    )
    
    # Show welcome screen if not started
    if not st.session_state.initialized:
        render_welcome_screen()
        return
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if not st.session_state.conversation_ended:
        if prompt := st.chat_input("Type your message here..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Generate response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response, ended = st.session_state.conversation_handler.process_message(prompt)
                    st.markdown(response)
            
            # Add assistant response
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Check if conversation ended
            if ended:
                st.session_state.conversation_ended = True
                # Auto-save on completion
                export_conversation()
    else:
        # Show completion message
        st.success("🎉 Thank you for completing the screening! Your information has been saved.")
        st.info("Click '🔄 New Chat' in the sidebar to start a new conversation.")


def render_welcome_screen():
    """Render the welcome screen with start button."""
    # Welcome container
    st.markdown("""
    <div style="text-align: center; padding: 2rem; background: rgba(30, 41, 59, 0.8); 
                border-radius: 16px; border: 1px solid rgba(99, 102, 241, 0.2); margin: 2rem 0;">
        <h2 style="color: #f1f5f9; margin-bottom: 1rem;">👋 Welcome, Candidate!</h2>
        <p style="color: #94a3b8; font-size: 1.1rem; margin-bottom: 1.5rem;">
            I'm your AI Hiring Assistant, here to help you through the initial screening process.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Information cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="text-align: center; padding: 1rem; background: rgba(99, 102, 241, 0.1); 
                    border-radius: 12px; border: 1px solid rgba(99, 102, 241, 0.3);">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">📝</div>
            <div style="color: #f1f5f9; font-weight: 600;">Step 1</div>
            <div style="color: #94a3b8; font-size: 0.9rem;">Share your basic info</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 1rem; background: rgba(139, 92, 246, 0.1); 
                    border-radius: 12px; border: 1px solid rgba(139, 92, 246, 0.3);">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">💻</div>
            <div style="color: #f1f5f9; font-weight: 600;">Step 2</div>
            <div style="color: #94a3b8; font-size: 0.9rem;">Tell us your tech stack</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="text-align: center; padding: 1rem; background: rgba(6, 182, 212, 0.1); 
                    border-radius: 12px; border: 1px solid rgba(6, 182, 212, 0.3);">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">❓</div>
            <div style="color: #f1f5f9; font-weight: 600;">Step 3</div>
            <div style="color: #94a3b8; font-size: 0.9rem;">Answer tech questions</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # What we'll collect
    st.markdown("""
    <div style="background: rgba(30, 41, 59, 0.6); padding: 1.5rem; border-radius: 12px; 
                border: 1px solid rgba(99, 102, 241, 0.2); margin: 1rem 0;">
        <h4 style="color: #06b6d4; margin-bottom: 1rem;">📋 What we'll collect:</h4>
        <div style="color: #f1f5f9; display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem;">
            <div>✓ Full Name</div>
            <div>✓ Email Address</div>
            <div>✓ Phone Number</div>
            <div>✓ Years of Experience</div>
            <div>✓ Desired Position(s)</div>
            <div>✓ Current Location</div>
            <div>✓ Tech Stack & Skills</div>
            <div>✓ Technical Assessment</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Privacy notice
    st.markdown(PRIVACY_NOTICE)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Start button - centered
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Start Conversation", use_container_width=True, type="primary"):
            start_conversation()
            st.rerun()
    
    # Time estimate
    st.markdown("""
    <div style="text-align: center; color: #64748b; margin-top: 1rem; font-size: 0.9rem;">
        ⏱️ This process takes approximately 5-10 minutes
    </div>
    """, unsafe_allow_html=True)


def start_conversation():
    """Initialize and start the conversation."""
    greeting = st.session_state.conversation_handler.get_initial_greeting()
    st.session_state.messages.append({"role": "assistant", "content": greeting})
    st.session_state.initialized = True


def main():
    """Main application entry point."""
    initialize_session_state()
    render_sidebar()
    render_chat_interface()


if __name__ == "__main__":
    main()

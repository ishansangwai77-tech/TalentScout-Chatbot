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

# Custom CSS for glassmorphism and liquid effects
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* Main theme colors */
    :root {
        --primary: #667eea;
        --secondary: #764ba2;
        --accent: #f093fb;
        --neon-blue: #00d4ff;
        --neon-pink: #ff006e;
        --neon-purple: #8338ec;
        --glass-bg: rgba(255, 255, 255, 0.05);
        --glass-border: rgba(255, 255, 255, 0.1);
    }
    
    /* Animated gradient background */
    .stApp {
        background: linear-gradient(-45deg, #0a0a1a, #1a0a2e, #0d1b2a, #1b263b, #0a0a1a);
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
        font-family: 'Inter', sans-serif;
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Floating orbs effect */
    .stApp::before {
        content: '';
        position: fixed;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: 
            radial-gradient(circle at 20% 80%, rgba(102, 126, 234, 0.15) 0%, transparent 50%),
            radial-gradient(circle at 80% 20%, rgba(240, 147, 251, 0.15) 0%, transparent 50%),
            radial-gradient(circle at 40% 40%, rgba(0, 212, 255, 0.1) 0%, transparent 40%);
        animation: floatOrbs 20s ease-in-out infinite;
        z-index: -1;
    }
    
    @keyframes floatOrbs {
        0%, 100% { transform: translate(0, 0) rotate(0deg); }
        33% { transform: translate(30px, -30px) rotate(120deg); }
        66% { transform: translate(-20px, 20px) rotate(240deg); }
    }
    
    /* Header with glow effect */
    .main-header {
        text-align: center;
        padding: 2rem 0;
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-shadow: 0 0 40px rgba(102, 126, 234, 0.5);
        animation: glowPulse 3s ease-in-out infinite;
    }
    
    @keyframes glowPulse {
        0%, 100% { filter: drop-shadow(0 0 20px rgba(102, 126, 234, 0.3)); }
        50% { filter: drop-shadow(0 0 40px rgba(240, 147, 251, 0.5)); }
    }
    
    .tagline {
        text-align: center;
        color: rgba(255, 255, 255, 0.7);
        font-size: 1.2rem;
        font-weight: 300;
        letter-spacing: 2px;
        margin-bottom: 2rem;
    }
    
    /* Glassmorphism cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 24px;
        box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
    }
    
    /* Chat messages with glass effect */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2) !important;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    
    .stChatMessage:hover {
        border-color: rgba(102, 126, 234, 0.3) !important;
        box-shadow: 0 12px 40px rgba(102, 126, 234, 0.15) !important;
        transform: translateY(-2px);
    }
    
    [data-testid="stChatMessageContent"] {
        color: rgba(255, 255, 255, 0.95) !important;
    }
    
    /* Chat input with neon glow */
    .stChatInputContainer {
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 16px !important;
        transition: all 0.3s ease;
    }
    
    .stChatInputContainer:focus-within {
        border-color: rgba(102, 126, 234, 0.5) !important;
        box-shadow: 0 0 30px rgba(102, 126, 234, 0.3) !important;
    }
    
    .stChatInputContainer input {
        color: white !important;
    }
    
    /* Sidebar with glass effect */
    [data-testid="stSidebar"] {
        background: rgba(10, 10, 26, 0.8) !important;
        backdrop-filter: blur(30px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: rgba(255, 255, 255, 0.9);
    }
    
    /* Phase badges with glow */
    .phase-badge {
        display: inline-block;
        padding: 0.4rem 1rem;
        border-radius: 25px;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }
    
    .phase-greeting { 
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
    }
    .phase-info { 
        background: linear-gradient(135deg, #764ba2, #f093fb);
        color: white;
        box-shadow: 0 4px 20px rgba(118, 75, 162, 0.4);
    }
    .phase-tech { 
        background: linear-gradient(135deg, #00d4ff, #667eea);
        color: white;
        box-shadow: 0 4px 20px rgba(0, 212, 255, 0.4);
    }
    .phase-questions { 
        background: linear-gradient(135deg, #f093fb, #ff006e);
        color: white;
        box-shadow: 0 4px 20px rgba(240, 147, 251, 0.4);
    }
    .phase-conclusion { 
        background: linear-gradient(135deg, #00d4ff, #00ff88);
        color: #0a0a1a;
        box-shadow: 0 4px 20px rgba(0, 212, 255, 0.4);
    }
    
    /* Liquid button effect */
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%) !important;
        background-size: 200% 200% !important;
        color: white !important;
        border: none !important;
        border-radius: 16px !important;
        padding: 0.8rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        letter-spacing: 1px !important;
        transition: all 0.4s ease !important;
        box-shadow: 0 8px 30px rgba(102, 126, 234, 0.4) !important;
    }
    
    .stButton button:hover {
        background-position: 100% 0 !important;
        transform: translateY(-4px) scale(1.02) !important;
        box-shadow: 0 15px 40px rgba(240, 147, 251, 0.5) !important;
    }
    
    /* Animated border for containers */
    @keyframes borderGlow {
        0%, 100% { border-color: rgba(102, 126, 234, 0.3); }
        50% { border-color: rgba(240, 147, 251, 0.5); }
    }
    
    /* Step cards with hover animation */
    .step-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    
    .step-card:hover {
        transform: translateY(-10px) scale(1.02);
        border-color: rgba(102, 126, 234, 0.5);
        box-shadow: 0 20px 50px rgba(102, 126, 234, 0.2);
    }
    
    /* Smooth fade-in animation */
    @keyframes fadeInUp {
        from { 
            opacity: 0; 
            transform: translateY(30px); 
        }
        to { 
            opacity: 1; 
            transform: translateY(0); 
        }
    }
    
    .animate-in {
        animation: fadeInUp 0.6s ease-out forwards;
    }
    
    /* Footer styling */
    .footer {
        text-align: center;
        color: rgba(255, 255, 255, 0.4);
        font-size: 0.8rem;
        padding: 2rem 0;
        margin-top: 2rem;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.02);
    }
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #667eea, #764ba2);
        border-radius: 4px;
    }
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

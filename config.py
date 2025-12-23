"""
Configuration module for TalentScout Hiring Assistant.
Contains all constants, settings, and configuration values.
"""

# Conversation phases
class ConversationPhase:
    """Enum-like class for conversation phases."""
    GREETING = "greeting"
    INFO_GATHERING = "info_gathering"
    TECH_STACK = "tech_stack"
    TECHNICAL_QUESTIONS = "technical_questions"
    CONCLUSION = "conclusion"
    ENDED = "ended"


# Required candidate information fields
CANDIDATE_FIELDS = [
    "full_name",
    "email",
    "phone",
    "years_of_experience",
    "desired_positions",
    "current_location",
    "tech_stack"
]

# Field display names and prompts
FIELD_PROMPTS = {
    "full_name": "What is your full name?",
    "email": "What is your email address?",
    "phone": "What is your phone number?",
    "years_of_experience": "How many years of professional experience do you have?",
    "desired_positions": "What position(s) are you interested in?",
    "current_location": "Where are you currently located?",
    "tech_stack": "Please tell me about your tech stack - including programming languages, frameworks, databases, and tools you're proficient in."
}

# Keywords that trigger conversation end
EXIT_KEYWORDS = [
    "bye", "goodbye", "exit", "quit", "end", "stop",
    "thank you", "thanks", "that's all", "no more",
    "end conversation", "close", "terminate"
]

# UI Configuration
APP_TITLE = "TalentScout Hiring Assistant"
APP_ICON = "🎯"
COMPANY_NAME = "TalentScout"
COMPANY_TAGLINE = "Your Partner in Tech Talent Acquisition"

# LLM Configuration
MAX_TOKENS = 1024
TEMPERATURE = 0.7
MODEL_NAME = "models/gemini-1.5-flash-latest"  # Full model path

# Technical questions configuration
MIN_QUESTIONS_PER_TECH = 3
MAX_QUESTIONS_PER_TECH = 5

# Data privacy notice
PRIVACY_NOTICE = """
🔒 **Privacy Notice**: Your information is handled securely and in compliance 
with data privacy standards. We only use your data for recruitment purposes 
and it will not be shared with third parties without your consent.
"""

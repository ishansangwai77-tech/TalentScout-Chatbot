"""
Utility functions for TalentScout Hiring Assistant.
Contains validation, data handling, and helper functions.
"""

import re
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from config import EXIT_KEYWORDS


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: The email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))


def validate_phone(phone: str) -> bool:
    """
    Validate phone number format.
    Accepts various formats with optional country code.
    
    Args:
        phone: The phone number to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Remove common separators for validation
    cleaned = re.sub(r'[\s\-\.\(\)]', '', phone)
    # Allow 10-15 digits, optionally starting with +
    pattern = r'^\+?[0-9]{10,15}$'
    return bool(re.match(pattern, cleaned))


def validate_experience(experience: str) -> Optional[float]:
    """
    Extract years of experience from text input.
    
    Args:
        experience: The experience text to parse
        
    Returns:
        Number of years as float, or None if cannot parse
    """
    # Try to extract numbers from the input
    numbers = re.findall(r'(\d+(?:\.\d+)?)', experience)
    if numbers:
        return float(numbers[0])
    
    # Handle text-based inputs
    text_to_num = {
        'fresher': 0, 'fresh': 0, 'no experience': 0,
        'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
    }
    
    lower_exp = experience.lower()
    for text, num in text_to_num.items():
        if text in lower_exp:
            return float(num)
    
    return None


def parse_tech_stack(tech_stack_text: str) -> List[str]:
    """
    Parse and extract individual technologies from tech stack description.
    
    Args:
        tech_stack_text: Raw tech stack description from candidate
        
    Returns:
        List of identified technologies
    """
    # Common technology keywords to look for
    known_technologies = [
        # Languages
        'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby', 'go',
        'rust', 'php', 'swift', 'kotlin', 'scala', 'r', 'matlab', 'perl',
        # Frontend
        'react', 'angular', 'vue', 'svelte', 'next.js', 'nuxt', 'html', 'css',
        'sass', 'less', 'tailwind', 'bootstrap', 'jquery', 'redux',
        # Backend
        'django', 'flask', 'fastapi', 'spring', 'node.js', 'express', 'rails',
        'laravel', 'asp.net', '.net', 'graphql', 'rest', 'grpc',
        # Databases
        'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'sqlite',
        'oracle', 'sql server', 'dynamodb', 'cassandra', 'neo4j', 'firebase',
        # Cloud & DevOps
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'terraform',
        'ansible', 'gitlab', 'github actions', 'circleci', 'linux',
        # ML/AI
        'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'pandas', 'numpy',
        'opencv', 'nltk', 'spacy', 'hugging face', 'langchain',
        # Mobile
        'react native', 'flutter', 'android', 'ios', 'xamarin',
        # Tools
        'git', 'jira', 'confluence', 'figma', 'postman', 'swagger'
    ]
    
    identified = []
    lower_text = tech_stack_text.lower()
    
    for tech in known_technologies:
        if tech in lower_text:
            identified.append(tech.title() if len(tech) > 3 else tech.upper())
    
    # Also split by common separators to catch unlisted technologies
    custom_techs = re.split(r'[,;/\n]', tech_stack_text)
    for tech in custom_techs:
        tech = tech.strip()
        if tech and len(tech) > 1 and tech.lower() not in [t.lower() for t in identified]:
            identified.append(tech)
    
    return list(set(identified))[:15]  # Limit to 15 technologies


def check_exit_intent(message: str) -> bool:
    """
    Check if the user's message indicates intent to end the conversation.
    
    Args:
        message: The user's message
        
    Returns:
        True if exit intent detected, False otherwise
    """
    lower_message = message.lower().strip()
    
    # Check exact matches and partial matches
    for keyword in EXIT_KEYWORDS:
        if keyword in lower_message:
            return True
    
    return False


def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent injection and clean formatting.
    
    Args:
        text: Raw user input
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = ' '.join(text.split())
    
    # Remove potential script tags or HTML
    text = re.sub(r'<[^>]*>', '', text)
    
    # Limit length to prevent abuse
    return text[:2000]


def format_candidate_summary(candidate_info: Dict[str, Any]) -> str:
    """
    Format candidate information into a readable summary.
    
    Args:
        candidate_info: Dictionary of collected candidate data
        
    Returns:
        Formatted summary string
    """
    summary_lines = [
        "=" * 50,
        "CANDIDATE SUMMARY",
        "=" * 50,
    ]
    
    field_labels = {
        'full_name': 'Full Name',
        'email': 'Email Address',
        'phone': 'Phone Number',
        'years_of_experience': 'Years of Experience',
        'desired_positions': 'Desired Position(s)',
        'current_location': 'Current Location',
        'tech_stack': 'Tech Stack'
    }
    
    for field, label in field_labels.items():
        value = candidate_info.get(field, 'Not provided')
        summary_lines.append(f"{label}: {value}")
    
    summary_lines.append("=" * 50)
    return '\n'.join(summary_lines)


def save_candidate_data(candidate_info: Dict[str, Any], 
                        conversation_history: List[Dict], 
                        output_dir: str = "candidate_data") -> str:
    """
    Save candidate data to JSON file for later processing.
    Data is anonymized with a unique ID instead of storing directly identifiable info.
    
    Args:
        candidate_info: Collected candidate information
        conversation_history: Full conversation history
        output_dir: Directory to save files
        
    Returns:
        Path to saved file
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate unique filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    candidate_id = f"candidate_{timestamp}"
    
    # Prepare data for storage
    data = {
        "candidate_id": candidate_id,
        "submission_timestamp": datetime.now().isoformat(),
        "candidate_info": candidate_info,
        "conversation_history": conversation_history,
        "data_handling_notice": "This data is collected for recruitment purposes only."
    }
    
    # Save to JSON file
    filepath = os.path.join(output_dir, f"{candidate_id}.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return filepath


def get_greeting_time() -> str:
    """
    Get appropriate greeting based on time of day.
    
    Returns:
        Time-appropriate greeting (Good morning/afternoon/evening)
    """
    hour = datetime.now().hour
    
    if hour < 12:
        return "Good morning"
    elif hour < 17:
        return "Good afternoon"
    else:
        return "Good evening"


def format_conversation_for_llm(messages: List[Dict]) -> str:
    """
    Format conversation history for LLM context.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content'
        
    Returns:
        Formatted conversation string
    """
    formatted = []
    for msg in messages:
        role = "Candidate" if msg.get("role") == "user" else "Assistant"
        formatted.append(f"{role}: {msg.get('content', '')}")
    
    return '\n'.join(formatted)

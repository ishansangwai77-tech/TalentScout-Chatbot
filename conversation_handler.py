"""
Conversation Handler for TalentScout Hiring Assistant.
Manages conversation state, flow control, and information gathering.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from config import (
    ConversationPhase, 
    CANDIDATE_FIELDS, 
    FIELD_PROMPTS,
    MIN_QUESTIONS_PER_TECH,
    MAX_QUESTIONS_PER_TECH
)
from utils import (
    validate_email, 
    validate_phone, 
    validate_experience, 
    parse_tech_stack,
    check_exit_intent,
    sanitize_input,
    format_candidate_summary,
    format_conversation_for_llm
)
from llm_client import LLMClient


@dataclass
class ConversationState:
    """
    Maintains the state of an ongoing conversation.
    Tracks collected information, current phase, and conversation history.
    """
    phase: str = ConversationPhase.GREETING
    candidate_info: Dict[str, str] = field(default_factory=dict)
    current_field_index: int = 0
    conversation_history: List[Dict] = field(default_factory=list)
    tech_stack_parsed: List[str] = field(default_factory=list)
    technical_questions_asked: bool = False
    questions_generated: str = ""
    awaiting_validation: Optional[str] = None


class ConversationHandler:
    """
    Handles the conversation flow and state management.
    Orchestrates between user input, LLM, and response generation.
    """
    
    def __init__(self, llm_client: LLMClient):
        """
        Initialize the conversation handler.
        
        Args:
            llm_client: Instance of LLMClient for generating responses
        """
        self.llm = llm_client
        self.state = ConversationState()
    
    def reset(self):
        """Reset the conversation state for a new session."""
        self.state = ConversationState()
        self.llm.reset_chat()
    
    def get_initial_greeting(self) -> str:
        """
        Get the initial greeting message to start the conversation.
        
        Returns:
            Greeting message from the LLM
        """
        greeting = self.llm.generate_greeting()
        self._add_to_history("assistant", greeting)
        self.state.phase = ConversationPhase.INFO_GATHERING
        return greeting
    
    def process_message(self, user_message: str) -> Tuple[str, bool]:
        """
        Process a user message and generate an appropriate response.
        
        Args:
            user_message: The user's input message
            
        Returns:
            Tuple of (response message, is_conversation_ended)
        """
        # Sanitize input
        user_message = sanitize_input(user_message)
        
        if not user_message:
            return "I didn't quite catch that. Could you please try again?", False
        
        # Add to history
        self._add_to_history("user", user_message)
        
        # Check for exit intent
        if check_exit_intent(user_message):
            return self._handle_exit(), True
        
        # Route based on current phase
        if self.state.phase == ConversationPhase.GREETING:
            return self._handle_greeting(user_message)
        
        elif self.state.phase == ConversationPhase.INFO_GATHERING:
            return self._handle_info_gathering(user_message)
        
        elif self.state.phase == ConversationPhase.TECH_STACK:
            return self._handle_tech_stack(user_message)
        
        elif self.state.phase == ConversationPhase.TECHNICAL_QUESTIONS:
            return self._handle_technical_questions(user_message)
        
        elif self.state.phase == ConversationPhase.CONCLUSION:
            return self._handle_conclusion(user_message)
        
        else:
            return self._handle_fallback(user_message)
    
    def _handle_greeting(self, message: str) -> Tuple[str, bool]:
        """Handle messages during greeting phase."""
        # Move to info gathering
        self.state.phase = ConversationPhase.INFO_GATHERING
        return self._handle_info_gathering(message)
    
    def _handle_info_gathering(self, message: str) -> Tuple[str, bool]:
        """Handle information gathering phase."""
        # Get current field to collect
        fields_to_collect = ['full_name', 'email', 'phone', 'years_of_experience', 
                            'desired_positions', 'current_location']
        
        # Process the previous field if we're collecting
        if self.state.current_field_index > 0:
            prev_field = fields_to_collect[self.state.current_field_index - 1]
            
            # Validate specific fields
            if prev_field == 'email' and not validate_email(message):
                response = self._generate_validation_response('email', message)
                self._add_to_history("assistant", response)
                return response, False
            
            elif prev_field == 'phone' and not validate_phone(message):
                response = self._generate_validation_response('phone', message)
                self._add_to_history("assistant", response)
                return response, False
            
            elif prev_field == 'years_of_experience':
                years = validate_experience(message)
                if years is not None:
                    self.state.candidate_info[prev_field] = str(years)
                else:
                    self.state.candidate_info[prev_field] = message
            else:
                self.state.candidate_info[prev_field] = message
        else:
            # First response is the name
            self.state.candidate_info['full_name'] = message
            self.state.current_field_index = 1
        
        # Check if we have all basic info
        if self.state.current_field_index >= len(fields_to_collect):
            # Move to tech stack phase
            self.state.phase = ConversationPhase.TECH_STACK
            response = self._generate_tech_stack_prompt()
            self._add_to_history("assistant", response)
            return response, False
        
        # Ask for next field
        current_field = fields_to_collect[self.state.current_field_index]
        self.state.current_field_index += 1
        
        response = self._generate_field_prompt(current_field, message)
        self._add_to_history("assistant", response)
        return response, False
    
    def _handle_tech_stack(self, message: str) -> Tuple[str, bool]:
        """Handle tech stack declaration phase."""
        # Parse the tech stack
        self.state.tech_stack_parsed = parse_tech_stack(message)
        self.state.candidate_info['tech_stack'] = message
        
        if not self.state.tech_stack_parsed:
            response = (
                "I'd like to understand your technical background better. Could you please "
                "specify the programming languages, frameworks, databases, or tools you work with? "
                "For example: Python, Django, PostgreSQL, Docker, etc."
            )
            self._add_to_history("assistant", response)
            return response, False
        
        # Move to technical questions phase
        self.state.phase = ConversationPhase.TECHNICAL_QUESTIONS
        
        # Generate technical questions
        experience = self.state.candidate_info.get('years_of_experience', '0')
        try:
            exp_years = float(experience)
        except:
            exp_years = 0
        
        position = self.state.candidate_info.get('desired_positions', 'Software Developer')
        
        questions = self.llm.generate_technical_questions(
            self.state.tech_stack_parsed,
            exp_years,
            position
        )
        
        self.state.questions_generated = questions
        self.state.technical_questions_asked = True
        
        # Create response with acknowledgment and questions
        tech_list = ", ".join(self.state.tech_stack_parsed)
        response = (
            f"Excellent! I can see you have experience with {tech_list}. "
            f"That's a great combination of skills!\n\n"
            f"Now, I'd like to ask you some technical questions to better understand "
            f"your proficiency. Please take your time with each question.\n\n"
            f"{questions}\n\n"
            f"Please share your thoughts on these questions. You can answer them in any order, "
            f"or let me know if you'd like to discuss any particular topic in more detail."
        )
        
        self._add_to_history("assistant", response)
        return response, False
    
    def _handle_technical_questions(self, message: str) -> Tuple[str, bool]:
        """Handle technical questions phase."""
        # Use LLM to evaluate and respond to technical answers
        context = format_conversation_for_llm(self.state.conversation_history[-6:])
        
        prompt = f"""The candidate has provided responses to technical questions.
        
Previous context:
{context}

Their latest response: {message}

Evaluate their response professionally:
1. Acknowledge their answer briefly
2. If they answered well, provide positive feedback
3. If they want to discuss more or have questions, engage appropriately
4. After sufficient technical discussion, ask if they have any questions about the role or company

Keep the response concise and professional. Do not provide detailed answers or solutions."""

        response = self.llm.generate_response(prompt)
        
        # Check if we should move to conclusion
        # This happens after the candidate indicates they've answered or have no more to add
        conclusion_indicators = ['that\'s all', 'done', 'finished', 'no more', 'nothing else', 
                                'that covers', 'i think that\'s it', 'any questions about']
        
        if any(indicator in message.lower() for indicator in conclusion_indicators):
            self.state.phase = ConversationPhase.CONCLUSION
            conclusion_response = self._generate_conclusion()
            self._add_to_history("assistant", conclusion_response)
            return conclusion_response, False
        
        self._add_to_history("assistant", response)
        return response, False
    
    def _handle_conclusion(self, message: str) -> Tuple[str, bool]:
        """Handle conclusion phase."""
        # Check if they want to end
        if check_exit_intent(message):
            return self._handle_exit(), True
        
        # Generate a final response
        response = self.llm.generate_response(
            f"The candidate said: '{message}'. Respond briefly and professionally, "
            f"then remind them that their application is complete and they can type 'bye' to end."
        )
        
        self._add_to_history("assistant", response)
        return response, False
    
    def _handle_exit(self) -> str:
        """Handle conversation exit."""
        self.state.phase = ConversationPhase.ENDED
        summary = format_candidate_summary(self.state.candidate_info)
        conclusion = self.llm.generate_conclusion(summary)
        self._add_to_history("assistant", conclusion)
        return conclusion
    
    def _handle_fallback(self, message: str) -> Tuple[str, bool]:
        """Handle unexpected inputs or unclear phases."""
        response = self.llm.generate_with_history(message, self.state.conversation_history)
        self._add_to_history("assistant", response)
        return response, False
    
    def _generate_field_prompt(self, field: str, previous_response: str) -> str:
        """Generate a prompt for collecting a specific field."""
        field_question = FIELD_PROMPTS.get(field, f"Could you please provide your {field}?")
        
        prompt = f"""The candidate just told us: "{previous_response}"
        
Now we need to ask for their {field.replace('_', ' ')}.
Generate a natural, conversational response that:
1. Briefly acknowledges what they said
2. Asks for: {field_question}

Keep it friendly and concise (1-2 sentences)."""

        return self.llm.generate_response(prompt)
    
    def _generate_validation_response(self, field: str, invalid_value: str) -> str:
        """Generate a response for invalid input."""
        if field == 'email':
            return (
                f"I notice the email '{invalid_value}' might have a small typo. "
                f"Could you please provide a valid email address? "
                f"For example: name@example.com"
            )
        elif field == 'phone':
            return (
                f"I'd like to make sure I have your correct phone number. "
                f"Could you please provide it in a standard format? "
                f"For example: +1234567890 or 123-456-7890"
            )
        return f"Could you please provide a valid {field}?"
    
    def _generate_tech_stack_prompt(self) -> str:
        """Generate the prompt to collect tech stack information."""
        name = self.state.candidate_info.get('full_name', 'there')
        
        return (
            f"Thank you for sharing that information, {name}! "
            f"Now, let's talk about your technical skills. "
            f"Please tell me about your tech stack - including the programming languages, "
            f"frameworks, databases, and tools you're proficient in. "
            f"The more detail you provide, the better I can assess your technical background."
        )
    
    def _generate_conclusion(self) -> str:
        """Generate the conclusion message."""
        summary = format_candidate_summary(self.state.candidate_info)
        return self.llm.generate_conclusion(summary)
    
    def _add_to_history(self, role: str, content: str):
        """Add a message to conversation history."""
        self.state.conversation_history.append({
            "role": role,
            "content": content
        })
    
    def get_candidate_info(self) -> Dict[str, str]:
        """Get collected candidate information."""
        return self.state.candidate_info.copy()
    
    def get_conversation_history(self) -> List[Dict]:
        """Get full conversation history."""
        return self.state.conversation_history.copy()
    
    def get_current_phase(self) -> str:
        """Get current conversation phase."""
        return self.state.phase
    
    def is_ended(self) -> bool:
        """Check if conversation has ended."""
        return self.state.phase == ConversationPhase.ENDED

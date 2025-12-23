"""
LLM Client Module for TalentScout Hiring Assistant.
Handles all interactions with the Groq API (Llama 3).
"""

import os
import time
from typing import List, Dict, Optional
from groq import Groq
from config import MAX_TOKENS, TEMPERATURE
from prompts import SYSTEM_PROMPT


class LLMClient:
    """
    Client for interacting with Groq API (Llama 3).
    Provides methods for generating responses with retry logic and error handling.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the LLM client with API key.
        
        Args:
            api_key: Groq API key. If None, reads from environment variable.
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.demo_mode = False
        self.client = None
        self.conversation_history = []
        
        # Check if API key is missing or placeholder
        if not self.api_key or self.api_key.startswith("YOUR_"):
            print("⚠️ No valid Groq API key found. Running in DEMO MODE.")
            self.demo_mode = True
            return
        
        # Initialize Groq client
        try:
            self.client = Groq(api_key=self.api_key)
            # Test the connection
            test_response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": "Say OK"}],
                max_tokens=10
            )
            if test_response.choices[0].message.content:
                print("✓ Connected to Groq API (Llama 3.3-70B)")
                # Initialize with system prompt
                self.conversation_history = [
                    {"role": "system", "content": SYSTEM_PROMPT}
                ]
        except Exception as e:
            print(f"⚠️ Groq API error: {str(e)[:100]}")
            print("Running in DEMO MODE.")
            self.demo_mode = True
    
    def generate_response(self, 
                         prompt: str, 
                         context: Optional[str] = None,
                         max_retries: int = 3) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The prompt to send to the model
            context: Optional additional context to include
            max_retries: Maximum number of retry attempts
            
        Returns:
            Generated response text
        """
        # Demo mode response
        if self.demo_mode:
            return self._get_demo_response(prompt)
        
        full_prompt = prompt
        if context:
            full_prompt = f"Context:\n{context}\n\nTask:\n{prompt}"
        
        for attempt in range(max_retries):
            try:
                # Add user message to history
                self.conversation_history.append({"role": "user", "content": full_prompt})
                
                response = self.client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=self.conversation_history,
                    max_tokens=MAX_TOKENS,
                    temperature=TEMPERATURE,
                )
                
                assistant_message = response.choices[0].message.content
                
                # Add assistant response to history
                self.conversation_history.append({"role": "assistant", "content": assistant_message})
                
                # Keep history manageable (last 20 messages)
                if len(self.conversation_history) > 21:
                    self.conversation_history = [self.conversation_history[0]] + self.conversation_history[-20:]
                
                return assistant_message
                
            except Exception as e:
                # Remove failed user message from history
                if self.conversation_history and self.conversation_history[-1]["role"] == "user":
                    self.conversation_history.pop()
                    
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 1
                    print(f"Retry attempt {attempt + 1} after {wait_time}s due to: {e}")
                    time.sleep(wait_time)
                else:
                    return self._get_demo_response(prompt)
        
        return self._get_demo_response(prompt)
    
    def generate_with_history(self, 
                             user_message: str, 
                             conversation_history: List[Dict]) -> str:
        """
        Generate a response considering full conversation history.
        """
        return self.generate_response(user_message)
    
    def generate_technical_questions(self, 
                                     tech_stack: List[str], 
                                     experience_years: float,
                                     position: str) -> str:
        """
        Generate technical questions based on candidate's tech stack.
        """
        if experience_years < 2:
            difficulty = "entry-level to intermediate"
            focus = "fundamental concepts, basic implementations, and learning ability"
        elif experience_years < 5:
            difficulty = "intermediate to advanced"
            focus = "practical application, problem-solving, and best practices"
        else:
            difficulty = "advanced to expert"
            focus = "system design, architecture decisions, and technical leadership"
        
        tech_list = ", ".join(tech_stack)
        
        prompt = f"""Generate technical interview questions for a candidate with the following profile:

Technologies: {tech_list}
Experience: {experience_years} years
Position: {position}
Difficulty Level: {difficulty}
Focus Areas: {focus}

For each technology, generate 3-5 questions that:
1. Test both theoretical understanding and practical knowledge
2. Include at least one scenario-based question
3. Cover common challenges and best practices
4. Are progressively challenging

Format the output clearly with technology headers and numbered questions.
Make questions specific and relevant to real-world scenarios."""

        return self.generate_response(prompt)
    
    def generate_greeting(self) -> str:
        """Generate an initial greeting message."""
        prompt = """Generate a warm, professional greeting for a new candidate starting 
the screening process. Include:
1. Welcome to TalentScout
2. Brief explanation of the screening purpose
3. Ask for their name to begin

Keep it concise (3-4 sentences), friendly, and professional."""

        return self.generate_response(prompt)
    
    def generate_conclusion(self, candidate_summary: str) -> str:
        """Generate a conclusion message."""
        prompt = f"""The screening process is complete. Generate a professional closing message.

Candidate Summary:
{candidate_summary}

Include:
1. Thank them for their time
2. Confirm their information has been recorded
3. Explain next steps (review within 5-7 business days)
4. Provide contact email: hr@talentscout.com
5. End on a positive, encouraging note

Keep it professional and warm."""

        return self.generate_response(prompt)
    
    def reset_chat(self):
        """Reset the chat session for a new conversation."""
        self.conversation_history = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
    
    def _get_demo_response(self, prompt: str) -> str:
        """Generate demo responses when API is unavailable."""
        prompt_lower = prompt.lower()
        
        if "greeting" in prompt_lower or "welcome" in prompt_lower:
            return (
                "👋 Welcome to TalentScout! I'm your AI Hiring Assistant.\n\n"
                "I'm here to help with your initial screening for tech positions. "
                "This process will take about 5-10 minutes.\n\n"
                "**Note:** Running in DEMO MODE - Connect a valid API key for full AI capabilities.\n\n"
                "Let's get started! **What is your full name?**"
            )
        
        if "technical" in prompt_lower or "question" in prompt_lower:
            return (
                "Based on your tech stack, here are some technical questions:\n\n"
                "**Python:**\n"
                "1. Explain the difference between `list` and `tuple` in Python.\n"
                "2. What is a decorator and how would you use it?\n"
                "3. How does Python handle memory management?\n\n"
                "Please share your thoughts on these questions!"
            )
        
        if "conclusion" in prompt_lower or "closing" in prompt_lower:
            return (
                "🎉 Thank you for completing the screening process!\n\n"
                "**Next Steps:**\n"
                "- Our team will review your responses within 5-7 business days\n"
                "- If selected, you'll receive an email for the next interview round\n"
                "- For questions, contact us at hr@talentscout.com\n\n"
                "We appreciate your time and interest in TalentScout. Good luck! 🍀"
            )
        
        return (
            "Thank you for your response! This is helpful information.\n\n"
            "Would you like to continue with the screening process?"
        )

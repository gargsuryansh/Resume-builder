import os
import streamlit as st
import logging
import google.generativeai as genai
import requests
import json

class LLMOrchestrator:
    """Manages LLM requests with automatic fallback (Gemini -> Groq -> Sarvam)"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Initialize Gemini
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        if self.google_api_key:
            genai.configure(api_key=self.google_api_key)
            self.gemini_model = genai.GenerativeModel("gemini-2.5-flash")
        else:
            self.gemini_model = None

        # Initialize Groq
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if self.groq_api_key:
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=self.groq_api_key)
            except ImportError:
                self.logger.warning("Groq SDK not installed. Fallback to Groq won't work unless installed.")
                self.groq_client = None
        else:
            self.groq_client = None

        # Initialize Sarvam AI
        self.sarvam_api_key = os.getenv("SARVAM_API_KEY")

    def generate_content(self, prompt):
        """
        Attempts to generate content using the defined primary and fallback sequence.
        Returns a tuple: (generated_text, provider_name)
        """
        # 1. Try Primary: Gemini
        if self.gemini_model:
            try:
                self.logger.info("Attempting generation using primary provider: Gemini")
                response = self.gemini_model.generate_content(prompt)
                
                # Check for safety blocks explicitly
                if hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
                    raise ValueError(f"Prompt blocked by Gemini safety filters: {response.prompt_feedback.block_reason}")
                
                # In newer versions of the SDK, accessing .text on a blocked response throws an exception,
                # which will be caught below. If it succeeds but is empty, we also want to fall back.
                try:
                    text = response.text
                except Exception as e:
                    raise ValueError(f"Failed to access text (likely safety blocked): {str(e)}")
                    
                if text:
                    return text.strip(), "Google Gemini 2.5 Flash"
                else:
                    raise ValueError("Gemini returned an empty response")
                    
            except Exception as e:
                # Identify the specific type of Gemini failure for logging
                error_str = str(e).lower()
                error_type = "Unknown Error"
                
                # We do string matching on the error since google exceptions can be deeply nested
                if "429" in error_str or "quota" in error_str or "exhausted" in error_str or "too many requests" in error_str:
                    error_type = "Rate Limited (429)"
                elif "503" in error_str or "unavailable" in error_str:
                    error_type = "API Unavailable (503)"
                elif "504" in error_str or "deadline" in error_str or "timeout" in error_str:
                    error_type = "Request Timeout (504)"
                elif "400" in error_str or "invalid argument" in error_str:
                    error_type = "Invalid Argument (400)"
                elif "403" in error_str or "permission" in error_str or "api_key" in error_str:
                    error_type = "Auth/Permission Denied (403)"
                elif "blocked" in error_str or "safety" in error_str or "finish_reason" in error_str:
                    error_type = "Safety/Content Filter Block"
                    
                self.logger.warning(f"⚠️ Gemini failed [{error_type}]: {str(e)}. Triggering Groq/Sarvam fallback sequence.")
        else:
            self.logger.warning("Gemini model not initialized (missing API key). Skipping to fallback.")

        # 2. Try Fallback 1: Groq
        if self.groq_client:
            try:
                self.logger.info("Attempting generation using first fallback: Groq (Llama 3.1 8B)")
                chat_completion = self.groq_client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.1-8b-instant",
                )
                if chat_completion.choices and chat_completion.choices[0].message.content:
                    return chat_completion.choices[0].message.content.strip(), "Groq (Llama 3.1 8B)"
            except Exception as e:
                self.logger.error(f"Groq generation failed: {str(e)}. Attempting next fallback.")

        # 3. Try Fallback 2: Sarvam AI
        if self.sarvam_api_key:
            try:
                self.logger.info("Attempting generation using second fallback: Sarvam AI")
                
                url = "https://api.sarvam.ai/v1/chat/completions"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.sarvam_api_key}"
                }
                # Use open-source/standard model structure format for Sarvam API wrapper if needed
                payload = {
                    "messages": [{"role": "user", "content": prompt}]
                }
                
                res = requests.post(url, headers=headers, json=payload, timeout=30)
                res.raise_for_status()
                data = res.json()
                
                if 'choices' in data and data['choices']:
                    return data['choices'][0]['message']['content'].strip(), "Sarvam AI"
            except Exception as e:
                self.logger.error(f"Sarvam AI generation failed: {str(e)}")

        raise Exception("All configured LLM providers failed or none are correctly configured.")

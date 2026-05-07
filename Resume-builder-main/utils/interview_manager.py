import os
import streamlit as st
from utils.llm_orchestrator import LLMOrchestrator
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io
import json
import re

class InterviewManager:
    """Manages the interview session state and evaluation logic"""
    
    def __init__(self):
        self.llm = LLMOrchestrator()
        self.styles = getSampleStyleSheet()

    def initialize_session(self, questions, role, company, target_length, language_mode):
        """Setup a new interview session"""
        st.session_state.interview = {
            "questions": questions,
            "role": role,
            "company": company,
            "target_length": target_length,
            "language_mode": language_mode,
            "current_step": "greeting", # greeting -> intro -> question_0 -> ... -> conclusion
            "question_index": 0,
            "transcript": [], # List of {"role": "AI/User", "text": "...", "score": 0, "feedback": "..."}
            "is_complete": False
        }

    def evaluate_answer(self, question, answer):
        """Use LLM to evaluate the user's answer with robust JSON parsing"""
        prompt = f"""
        Role: {st.session_state.interview.get('role', 'Candidate')}
        Company: {st.session_state.interview.get('company', 'Target Company')}
        
        Question: {question}
        User's Answer: {answer}
        
        Critically evaluate this response. Provide a realistic score and helpful feedback.
        
        Return the result in strictly valid JSON format:
        {{
            "score": Integer (1-10),
            "feedback": "2-3 sentences of objective analysis",
            "improvement": "One specific actionable tip"
        }}
        """
        try:
            response, _ = self.llm.generate_content(prompt)
            # Find JSON block
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                clean_json = match.group()
                # Remove common LLM artifacts
                clean_json = clean_json.replace("```json", "").replace("```", "").strip()
                data = json.loads(clean_json)
                # Ensure all keys exist
                return {
                    "score": int(data.get("score", 5)),
                    "feedback": data.get("feedback", "Answer recorded."),
                    "improvement": data.get("improvement", "N/A")
                }
            return {"score": 5, "feedback": "Answer captured for report.", "improvement": "N/A"}
        except Exception as e:
            print(f"Evaluation failed: {str(e)}")
            return {"score": 5, "feedback": "Answer recorded successfully.", "improvement": "N/A"}

    def generate_pdf_report(self):
        """Generate a PDF report of the interview session"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        # Title
        title_style = self.styles['Heading1']
        title_style.alignment = 1 # Center
        elements.append(Paragraph(f"Interview Performance Report", title_style))
        elements.append(Spacer(1, 12))
        
        # Metadata
        meta_style = self.styles['Normal']
        elements.append(Paragraph(f"<b>Candidate:</b> {st.session_state.get('candidate_name', 'User')}", meta_style))
        elements.append(Paragraph(f"<b>Role:</b> {st.session_state.interview['role']}", meta_style))
        elements.append(Paragraph(f"<b>Company:</b> {st.session_state.interview['company']}", meta_style))
        elements.append(Spacer(1, 24))
        
        # Transcript & Scores
        total_score = 0
        questions_count = 0
        
        for item in st.session_state.interview['transcript']:
            if item['role'] == "AI" and "question_idx" in item:
                elements.append(Paragraph(f"<b>Question {item['question_idx'] + 1}:</b> {item['text']}", self.styles['Normal']))
            elif item['role'] == "User":
                elements.append(Paragraph(f"<b>Your Answer:</b> {item['text']}", self.styles['Normal']))
                score = item.get('score', 0)
                feedback = item.get('feedback', 'No feedback available')
                improvement = item.get('improvement', 'N/A')
                
                elements.append(Paragraph(f"<b>Score:</b> {score}/10", self.styles['Normal']))
                elements.append(Paragraph(f"<b>Feedback:</b> {feedback}", self.styles['Italic']))
                elements.append(Paragraph(f"<b>Pro Tip:</b> {improvement}", self.styles['Normal']))
                elements.append(Spacer(1, 12))
                
                total_score += score
                questions_count += 1
        
        # Final Score
        if questions_count > 0:
            avg_score = total_score / questions_count
            elements.append(Spacer(1, 24))
            elements.append(Paragraph(f"<b>Final Average Score: {avg_score:.1f}/10</b>", self.styles['Heading2']))
        
        doc.build(elements)
        buffer.seek(0)
        return buffer

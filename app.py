"""
Smart Resume AI - Main Application
"""
import time
from PIL import Image
from jobs.job_search import render_job_search
from datetime import datetime
from ui_components import (
    apply_modern_styles, hero_section, feature_card,
    page_header, render_analytics_section, progress_bar
)
from feedback.feedback import FeedbackManager
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt
from docx import Document
import io
import base64
import plotly.graph_objects as go
from streamlit_lottie import st_lottie
import requests
from dashboard.dashboard import DashboardManager
from config.courses import COURSES_BY_CATEGORY, RESUME_VIDEOS, INTERVIEW_VIDEOS, get_courses_for_role, get_category_for_role
from config.job_roles import JOB_ROLES
from config.database import (
    get_database_connection, save_resume_data, save_analysis_data,
    init_database, verify_admin, log_admin_action, save_ai_analysis_data,
    get_detailed_ai_analysis_stats
)
from utils.ai_resume_analyzer import AIResumeAnalyzer
from utils.resume_builder import ResumeBuilder
from utils.resume_analyzer import ResumeAnalyzer
import traceback
import plotly.express as px
import pandas as pd
import json
import streamlit as st
import datetime
from streamlit_mic_recorder import mic_recorder
from utils.audio_utils import AudioUtils
from utils.interview_manager import InterviewManager

# Set page config at the very beginning
st.set_page_config(
    page_title="Smart Resume AI",
    page_icon="🚀",
    layout="wide"
)


class ResumeApp:
    def __init__(self):
        """Initialize the application"""
        if 'form_data' not in st.session_state:
            st.session_state.form_data = {
                'personal_info': {
                    'full_name': '',
                    'email': '',
                    'phone': '',
                    'location': '',
                    'linkedin': '',
                    'portfolio': ''
                },
                'summary': '',
                'experiences': [],
                'education': [],
                'projects': [],
                'skills_categories': {
                    'technical': [],
                    'soft': [],
                    'languages': [],
                    'tools': []
                }
            }

        # Initialize navigation state
        if 'page' not in st.session_state:
            st.session_state.page = 'home'

        # Initialize admin state
        if 'is_admin' not in st.session_state:
            st.session_state.is_admin = False

        self.pages = {
            "🏠 HOME": self.render_home,
            "🔍 RESUME ANALYZER": self.render_analyzer,
            "📝 RESUME BUILDER": self.render_builder,
            "📊 DASHBOARD": self.render_dashboard,
            "🤝 RECRUITERS": self.render_recruiter_page,
            "🎯 JOB SEARCH": self.render_job_search,
            "👤 MY PROFILE": self.render_profile_page,
            "💬 FEEDBACK": self.render_feedback_page,
            "ℹ️ ABOUT": self.render_about
        }

        # Initialize dashboard manager
        self.dashboard_manager = DashboardManager()

        self.analyzer = ResumeAnalyzer()
        self.ai_analyzer = AIResumeAnalyzer()
        self.builder = ResumeBuilder()
        self.job_roles = JOB_ROLES

        # Initialize session state
        if 'user_id' not in st.session_state:
            st.session_state.user_id = 'default_user'
        if 'selected_role' not in st.session_state:
            st.session_state.selected_role = None

        # Initialize database
        init_database()

        # Load external CSS
        with open('style/style.css') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

        # Load Google Fonts
        st.markdown("""
            <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&family=Poppins:wght@400;500;600&display=swap" rel="stylesheet">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
        """, unsafe_allow_html=True)

        if 'resume_data' not in st.session_state:
            st.session_state.resume_data = []
        if 'ai_analysis_stats' not in st.session_state:
            st.session_state.ai_analysis_stats = {
                'score_distribution': {},
                'total_analyses': 0,
                'average_score': 0
            }

    def load_lottie_url(self, url: str):
        """Load Lottie animation from URL"""
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()

    def apply_global_styles(self):
        st.markdown("""
        <style>
        /* Custom Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: #1a1a1a;
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb {
            background: #4CAF50;
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: #45a049;
        }

        /* Global Styles */
        .main-header {
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            padding: 2rem;
            border-radius: 15px;
            margin-bottom: 2rem;
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
            text-align: center;
            position: relative;
            overflow: hidden;
        }

        .main-header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(45deg, transparent 0%, rgba(255,255,255,0.1) 100%);
            z-index: 1;
        }

        .main-header h1 {
            color: white;
            font-size: 2.5rem;
            font-weight: 600;
            margin: 0;
            position: relative;
            z-index: 2;
        }

        /* Template Card Styles */
        .template-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 2rem;
            padding: 1rem;
        }

        .template-card {
            background: rgba(45, 45, 45, 0.9);
            border-radius: 20px;
            padding: 2rem;
            position: relative;
            overflow: hidden;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .template-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
            border-color: #4CAF50;
        }

        .template-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(45deg, transparent 0%, rgba(76,175,80,0.1) 100%);
            z-index: 1;
        }

        .template-icon {
            font-size: 3rem;
            color: #4CAF50;
            margin-bottom: 1.5rem;
            position: relative;
            z-index: 2;
        }

        .template-title {
            font-size: 1.8rem;
            font-weight: 600;
            color: white;
            margin-bottom: 1rem;
            position: relative;
            z-index: 2;
        }

        .template-description {
            color: #aaa;
            margin-bottom: 1.5rem;
            position: relative;
            z-index: 2;
            line-height: 1.6;
        }

        /* Feature List Styles */
        .feature-list {
            list-style: none;
            padding: 0;
            margin: 1.5rem 0;
            position: relative;
            z-index: 2;
        }

        .feature-item {
            display: flex;
            align-items: center;
            margin-bottom: 1rem;
            color: #ddd;
            font-size: 0.95rem;
        }

        .feature-icon {
            color: #4CAF50;
            margin-right: 0.8rem;
            font-size: 1.1rem;
        }

        /* Button Styles */
        .action-button {
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            color: white;
            padding: 1rem 2rem;
            border-radius: 50px;
            border: none;
            font-weight: 500;
            cursor: pointer;
            width: 100%;
            text-align: center;
            position: relative;
            overflow: hidden;
            z-index: 2;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .action-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(76,175,80,0.3);
        }

        .action-button::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.2) 50%, transparent 100%);
            transition: all 0.6s ease;
        }

        .action-button:hover::before {
            left: 100%;
        }

        /* Form Section Styles */
        .form-section {
            background: rgba(45, 45, 45, 0.9);
            border-radius: 20px;
            padding: 2rem;
            margin: 2rem 0;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }

        .form-section-title {
            font-size: 1.8rem;
            font-weight: 600;
            color: white;
            margin-bottom: 1.5rem;
            padding-bottom: 0.8rem;
            border-bottom: 2px solid #4CAF50;
        }

        .form-group {
            margin-bottom: 1.5rem;
        }

        .form-label {
            color: #ddd;
            font-weight: 500;
            margin-bottom: 0.8rem;
            display: block;
        }

        .form-input {
            width: 100%;
            padding: 1rem;
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.1);
            background: rgba(30, 30, 30, 0.9);
            color: white;
            transition: all 0.3s ease;
        }

        .form-input:focus {
            border-color: #4CAF50;
            box-shadow: 0 0 0 2px rgba(76,175,80,0.2);
            outline: none;
        }

        /* Skill Tags */
        .skill-tag-container {
            display: flex;
            flex-wrap: wrap;
            gap: 0.8rem;
            margin-top: 1rem;
        }

        .skill-tag {
            background: rgba(76,175,80,0.1);
            color: #4CAF50;
            padding: 0.6rem 1.2rem;
            border-radius: 50px;
            border: 1px solid #4CAF50;
            font-size: 0.9rem;
            transition: all 0.3s ease;
            cursor: pointer;
        }

        .skill-tag:hover {
            background: #4CAF50;
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(76,175,80,0.2);
        }

        /* Progress Circle */
        .progress-container {
            position: relative;
            width: 150px;
            height: 150px;
            margin: 2rem auto;
        }

        .progress-circle {
            transform: rotate(-90deg);
            width: 100%;
            height: 100%;
        }

        .progress-circle circle {
            fill: none;
            stroke-width: 8;
            stroke-linecap: round;
            stroke: #4CAF50;
            transform-origin: 50% 50%;
            transition: all 0.3s ease;
        }

        .progress-text {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 1.5rem;
            font-weight: 600;
            color: white;
        }
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        .feature-card {
            background-color: #1e1e1e;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        /* Animations */
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .animate-slide-in {
            animation: slideIn 0.6s cubic-bezier(0.4, 0, 0.2, 1) forwards;
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .template-container {
                grid-template-columns: 1fr;
            }

            .main-header {
                padding: 1.5rem;
            }

            .main-header h1 {
                font-size: 2rem;
            }

            .template-card {
                padding: 1.5rem;
            }

            .action-button {
                padding: 0.8rem 1.6rem;
            }
        }
        </style>
        """, unsafe_allow_html=True)
        
    def add_footer(self):
        """Add a footer to all pages"""
        st.markdown("<hr style='margin-top: 50px; margin-bottom: 20px;'>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col2:
            # GitHub star button with lottie animation
            # st.markdown("""
            # <div style='display: flex; justify-content: center; align-items: center; margin-bottom: 10px;'>
            #     <a href='https://github.com/Hunterdii/Smart-AI-Resume-Analyzer' target='_blank' style='text-decoration: none;'>
            #         <div style='display: flex; align-items: center; background-color: #24292e; padding: 5px 10px; border-radius: 5px; transition: all 0.3s ease;'>
            #             <svg height="16" width="16" viewBox="0 0 16 16" version="1.1" style='margin-right: 5px;'>
            #                 <path fill-rule="evenodd" d="M8 .25a.75.75 0 01.673.418l1.882 3.815 4.21.612a.75.75 0 01.416 1.279l-3.046 2.97.719 4.192a.75.75 0 01-1.088.791L8 12.347l-3.766 1.98a.75.75 0 01-1.088-.79l.72-4.194L.818 6.374a.75.75 0 01.416-1.28l4.21-.611L7.327.668A.75.75 0 018 .25z" fill="gold"></path>
            #             </svg>
            #             <span style='color: white; font-size: 14px;'>Star this repo</span>
            #         </div>
            #     </a>
            # </div>
            # """, unsafe_allow_html=True)
            
            # Footer text
            st.markdown("""
            <p style='text-align: center;'>
               
            </p>
            <p style='text-align: center; font-size: 12px; color: #888888;'>
                "Get started to explore more "
            </p>
            """, unsafe_allow_html=True)

    def load_image(self, image_name):
        """Load image from static directory"""
        try:
            image_path = f"c:/Users/shree/Downloads/smart-resume-ai/{image_name}"
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            encoded = base64.b64encode(image_bytes).decode()
            return f"data:image/png;base64,{encoded}"
        except Exception as e:
            print(f"Error loading image {image_name}: {e}")
            return None

    def export_to_excel(self):
        """Export resume data to Excel"""
        conn = get_database_connection()

        # Get resume data with analysis
        query = """
            SELECT
                rd.name, rd.email, rd.phone, rd.linkedin, rd.github, rd.portfolio,
                rd.summary, rd.target_role, rd.target_category,
                rd.education, rd.experience, rd.projects, rd.skills,
                ra.ats_score, ra.keyword_match_score, ra.format_score, ra.section_score,
                ra.missing_skills, ra.recommendations,
                rd.created_at
            FROM resume_data rd
            LEFT JOIN resume_analysis ra ON rd.id = ra.resume_id
        """

        try:
            # Read data into DataFrame
            df = pd.read_sql_query(query, conn)

            # Create Excel writer object
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Resume Data')

            return output.getvalue()
        except Exception as e:
            print(f"Error exporting to Excel: {str(e)}")
            return None
        finally:
            conn.close()

    def render_dashboard(self):
        """Render the dashboard page"""
        self.dashboard_manager.render_dashboard()

        st.toast("Check out these repositories: [Awesome Hacking](https://github.com/Hunterdii/Awesome-Hacking)", icon="ℹ️")


    def render_empty_state(self, icon, message):
        """Render an empty state with icon and message"""
        return f"""
            <div style='text-align: center; padding: 2rem; color: #666;'>
                <i class='{icon}' style='font-size: 2rem; margin-bottom: 1rem; color: #00bfa5;'></i>
                <p style='margin: 0;'>{message}</p>
            </div>
        """

    def analyze_resume(self, resume_text):
        """Analyze resume and store results"""
        analytics = self.analyzer.analyze_resume(resume_text)
        st.session_state.analytics_data = analytics
        return analytics

    def handle_resume_upload(self):
        """Handle resume upload and analysis"""
        uploaded_file = st.file_uploader(
            "Upload your resume", type=['pdf', 'docx'])

        if uploaded_file is not None:
            try:
                # Extract text from resume
                if uploaded_file.type == "application/pdf":
                    resume_text = extract_text_from_pdf(uploaded_file)
                else:
                    resume_text = extract_text_from_docx(uploaded_file)

                # Store resume data
                st.session_state.resume_data = {
                    'filename': uploaded_file.name,
                    'content': resume_text,
                    'upload_time': datetime.now().isoformat()
                }

                # Analyze resume
                analytics = self.analyze_resume(resume_text)

                return True
            except Exception as e:
                st.error(f"Error processing resume: {str(e)}")
                return False
        return False

    def render_builder(self):
        page_header(
            "Precision Builder",
            "Craft your professional story with AI-optimized templates"
        )

        # Template selection
        with st.container():
            st.markdown('<div class="glass-card" style="margin-bottom: 2rem;">', unsafe_allow_html=True)
            template_options = ["Modern", "Professional", "Minimal", "Creative"]
            selected_template = st.selectbox("Select Your Visual Identity", template_options)
            st.markdown('</div>', unsafe_allow_html=True)

        # Personal Information
        st.markdown('<h3 style="color: var(--primary); margin-bottom: 1rem;">👤 Personal Information</h3>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            # Get existing values from session state
            existing_name = st.session_state.form_data['personal_info']['full_name']
            existing_email = st.session_state.form_data['personal_info']['email']
            existing_phone = st.session_state.form_data['personal_info']['phone']

            # Input fields with existing values
            full_name = st.text_input("Full Name", value=existing_name)
            email = st.text_input(
    "Email",
    value=existing_email,
     key="email_input")
            phone = st.text_input("Phone", value=existing_phone)

            # Immediately update session state after email input
            if 'email_input' in st.session_state:
                st.session_state.form_data['personal_info']['email'] = st.session_state.email_input

        with col2:
            # Get existing values from session state
            existing_location = st.session_state.form_data['personal_info']['location']
            existing_linkedin = st.session_state.form_data['personal_info']['linkedin']
            existing_portfolio = st.session_state.form_data['personal_info']['portfolio']

            # Input fields with existing values
            location = st.text_input("Location", value=existing_location)
            linkedin = st.text_input("LinkedIn URL", value=existing_linkedin)
            portfolio = st.text_input(
    "Portfolio Website", value=existing_portfolio)

        # Update personal info in session state
        st.session_state.form_data['personal_info'] = {
            'full_name': full_name,
            'email': email,
            'phone': phone,
            'location': location,
            'linkedin': linkedin,
            'portfolio': portfolio
        }

        # Professional Summary
        st.subheader("Professional Summary")
        summary = st.text_area("Professional Summary", value=st.session_state.form_data.get('summary', ''), height=150,
                             help="Write a brief summary highlighting your key skills and experience")

        # Experience Section
        st.subheader("Work Experience")
        if 'experiences' not in st.session_state.form_data:
            st.session_state.form_data['experiences'] = []

        if st.button("Add Experience"):
            st.session_state.form_data['experiences'].append({
                'company': '',
                'position': '',
                'start_date': '',
                'end_date': '',
                'description': '',
                'responsibilities': [],
                'achievements': []
            })

        for idx, exp in enumerate(st.session_state.form_data['experiences']):
            with st.expander(f"Experience {idx + 1}", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    exp['company'] = st.text_input(
    "Company Name",
    key=f"company_{idx}",
    value=exp.get(
        'company',
         ''))
                    exp['position'] = st.text_input(
    "Position", key=f"position_{idx}", value=exp.get(
        'position', ''))
                with col2:
                    exp['start_date'] = st.text_input(
    "Start Date", key=f"start_date_{idx}", value=exp.get(
        'start_date', ''))
                    exp['end_date'] = st.text_input(
    "End Date", key=f"end_date_{idx}", value=exp.get(
        'end_date', ''))

                exp['description'] = st.text_area("Role Overview", key=f"desc_{idx}",
                                                value=exp.get(
                                                    'description', ''),
                                                help="Brief overview of your role and impact")

                # Responsibilities
                st.markdown("##### Key Responsibilities")
                resp_text = st.text_area("Enter responsibilities (one per line)",
                                       key=f"resp_{idx}",
                                       value='\n'.join(
                                           exp.get('responsibilities', [])),
                                       height=100,
                                       help="List your main responsibilities, one per line")
                exp['responsibilities'] = [r.strip()
                                                   for r in resp_text.split('\n') if r.strip()]

                # Achievements
                st.markdown("##### Key Achievements")
                achv_text = st.text_area("Enter achievements (one per line)",
                                       key=f"achv_{idx}",
                                       value='\n'.join(
                                           exp.get('achievements', [])),
                                       height=100,
                                       help="List your notable achievements, one per line")
                exp['achievements'] = [a.strip()
                                               for a in achv_text.split('\n') if a.strip()]

                if st.button("Remove Experience", key=f"remove_exp_{idx}"):
                    st.session_state.form_data['experiences'].pop(idx)
                    st.rerun()

        # Projects Section
        st.subheader("Projects")
        if 'projects' not in st.session_state.form_data:
            st.session_state.form_data['projects'] = []

        if st.button("Add Project"):
            st.session_state.form_data['projects'].append({
                'name': '',
                'technologies': '',
                'description': '',
                'responsibilities': [],
                'achievements': [],
                'link': ''
            })

        for idx, proj in enumerate(st.session_state.form_data['projects']):
            with st.expander(f"Project {idx + 1}", expanded=True):
                proj['name'] = st.text_input(
    "Project Name",
    key=f"proj_name_{idx}",
    value=proj.get(
        'name',
         ''))
                proj['technologies'] = st.text_input("Technologies Used", key=f"proj_tech_{idx}",
                                                   value=proj.get(
                                                       'technologies', ''),
                                                   help="List the main technologies, frameworks, and tools used")

                proj['description'] = st.text_area("Project Overview", key=f"proj_desc_{idx}",
                                                 value=proj.get(
                                                     'description', ''),
                                                 help="Brief overview of the project and its goals")

                # Project Responsibilities
                st.markdown("##### Key Responsibilities")
                proj_resp_text = st.text_area("Enter responsibilities (one per line)",
                                            key=f"proj_resp_{idx}",
                                            value='\n'.join(
                                                proj.get('responsibilities', [])),
                                            height=100,
                                            help="List your main responsibilities in the project")
                proj['responsibilities'] = [r.strip()
                                                    for r in proj_resp_text.split('\n') if r.strip()]

                # Project Achievements
                st.markdown("##### Key Achievements")
                proj_achv_text = st.text_area("Enter achievements (one per line)",
                                            key=f"proj_achv_{idx}",
                                            value='\n'.join(
                                                proj.get('achievements', [])),
                                            height=100,
                                            help="List the project's key achievements and your contributions")
                proj['achievements'] = [a.strip()
                                                for a in proj_achv_text.split('\n') if a.strip()]

                proj['link'] = st.text_input("Project Link (optional)", key=f"proj_link_{idx}",
                                           value=proj.get('link', ''),
                                           help="Link to the project repository, demo, or documentation")

                if st.button("Remove Project", key=f"remove_proj_{idx}"):
                    st.session_state.form_data['projects'].pop(idx)
                    st.rerun()

        # Education Section
        st.subheader("Education")
        if 'education' not in st.session_state.form_data:
            st.session_state.form_data['education'] = []

        if st.button("Add Education"):
            st.session_state.form_data['education'].append({
                'school': '',
                'degree': '',
                'field': '',
                'graduation_date': '',
                'gpa': '',
                'achievements': []
            })

        for idx, edu in enumerate(st.session_state.form_data['education']):
            with st.expander(f"Education {idx + 1}", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    edu['school'] = st.text_input(
    "School/University",
    key=f"school_{idx}",
    value=edu.get(
        'school',
         ''))
                    edu['degree'] = st.text_input(
    "Degree", key=f"degree_{idx}", value=edu.get(
        'degree', ''))
                with col2:
                    edu['field'] = st.text_input(
    "Field of Study",
    key=f"field_{idx}",
    value=edu.get(
        'field',
         ''))
                    edu['graduation_date'] = st.text_input("Graduation Date", key=f"grad_date_{idx}",
                                                         value=edu.get('graduation_date', ''))

                edu['gpa'] = st.text_input(
    "GPA (optional)",
    key=f"gpa_{idx}",
    value=edu.get(
        'gpa',
         ''))

                # Educational Achievements
                st.markdown("##### Achievements & Activities")
                edu_achv_text = st.text_area("Enter achievements (one per line)",
                                           key=f"edu_achv_{idx}",
                                           value='\n'.join(
                                               edu.get('achievements', [])),
                                           height=100,
                                           help="List academic achievements, relevant coursework, or activities")
                edu['achievements'] = [a.strip()
                                               for a in edu_achv_text.split('\n') if a.strip()]

                if st.button("Remove Education", key=f"remove_edu_{idx}"):
                    st.session_state.form_data['education'].pop(idx)
                    st.rerun()

        # Skills Section
        st.subheader("Skills")
        if 'skills_categories' not in st.session_state.form_data:
            st.session_state.form_data['skills_categories'] = {
                'technical': [],
                'soft': [],
                'languages': [],
                'tools': []
            }

        col1, col2 = st.columns(2)
        with col1:
            tech_skills = st.text_area("Technical Skills (one per line)",
                                     value='\n'.join(
    st.session_state.form_data['skills_categories']['technical']),
                                     height=150,
                                     help="Programming languages, frameworks, databases, etc.")
            st.session_state.form_data['skills_categories']['technical'] = [
                s.strip() for s in tech_skills.split('\n') if s.strip()]

            soft_skills = st.text_area("Soft Skills (one per line)",
                                     value='\n'.join(
    st.session_state.form_data['skills_categories']['soft']),
                                     height=150,
                                     help="Leadership, communication, problem-solving, etc.")
            st.session_state.form_data['skills_categories']['soft'] = [
                s.strip() for s in soft_skills.split('\n') if s.strip()]

        with col2:
            languages = st.text_area("Languages (one per line)",
                                   value='\n'.join(
    st.session_state.form_data['skills_categories']['languages']),
                                   height=150,
                                   help="Programming or human languages with proficiency level")
            st.session_state.form_data['skills_categories']['languages'] = [
                l.strip() for l in languages.split('\n') if l.strip()]

            tools = st.text_area("Tools & Technologies (one per line)",
                               value='\n'.join(
    st.session_state.form_data['skills_categories']['tools']),
                               height=150,
                               help="Development tools, software, platforms, etc.")
            st.session_state.form_data['skills_categories']['tools'] = [
                t.strip() for t in tools.split('\n') if t.strip()]

        # Update form data in session state
        st.session_state.form_data.update({
            'summary': summary
        })

        # Generate Resume button
        if st.button("Generate Resume 📄", type="primary"):
            print("Validating form data...")
            print(f"Session state form data: {st.session_state.form_data}")
            print(f"Email input value: {st.session_state.get('email_input', '')}")

            # Get the current values from form
            current_name = st.session_state.form_data['personal_info']['full_name'].strip(
            )
            current_email = st.session_state.email_input if 'email_input' in st.session_state else ''

            print(f"Current name: {current_name}")
            print(f"Current email: {current_email}")

            # Validate required fields
            if not current_name:
                st.error("⚠️ Please enter your full name.")
                return

            if not current_email:
                st.error("⚠️ Please enter your email address.")
                return

            # Update email in form data one final time
            st.session_state.form_data['personal_info']['email'] = current_email

            try:
                print("Preparing resume data...")
                # Prepare resume data with current form values
                resume_data = {
                    "personal_info": st.session_state.form_data['personal_info'],
                    "summary": st.session_state.form_data.get('summary', '').strip(),
                    "experience": st.session_state.form_data.get('experiences', []),
                    "education": st.session_state.form_data.get('education', []),
                    "projects": st.session_state.form_data.get('projects', []),
                    "skills": st.session_state.form_data.get('skills_categories', {
                        'technical': [],
                        'soft': [],
                        'languages': [],
                        'tools': []
                    }),
                    "template": selected_template
                }

                print(f"Resume data prepared: {resume_data}")

                try:
                    # Generate resume
                    resume_buffer = self.builder.generate_resume(resume_data)
                    if resume_buffer:
                        try:
                            # Save resume data to database
                            save_resume_data(resume_data)

                            # Offer the resume for download
                            st.success("✅ Resume generated successfully!")

                            # Show snowflake effect
                            st.snow()

                            st.download_button(
                                label="Download Resume 📥",
                                data=resume_buffer,
                                file_name=f"{current_name.replace(' ', '_')}_resume.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                on_click=lambda: st.balloons()
                            )
                        except Exception as db_error:
                            print(f"Warning: Failed to save to database: {str(db_error)}")
                            # Still allow download even if database save fails
                            st.warning(
                                "⚠️ Resume generated but couldn't be saved to database")
                            
                            # Show balloons effect
                            st.balloons()

                            st.download_button(
                                label="Download Resume 📥",
                                data=resume_buffer,
                                file_name=f"{current_name.replace(' ', '_')}_resume.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                on_click=lambda: st.balloons()
                            )
                    else:
                        st.error(
                            "❌ Failed to generate resume. Please try again.")
                        print("Resume buffer was None")
                except Exception as gen_error:
                    print(f"Error during resume generation: {str(gen_error)}")
                    print(f"Full traceback: {traceback.format_exc()}")
                    st.error(f"❌ Error generating resume: {str(gen_error)}")

            except Exception as e:
                print(f"Error preparing resume data: {str(e)}")
                print(f"Full traceback: {traceback.format_exc()}")
                st.error(f"❌ Error preparing resume data: {str(e)}")

        st.toast("Check out these repositories: [30-Days-Of-Rust](https://github.com/Hunterdii/30-Days-Of-Rust)", icon="ℹ️")

    def render_about(self):
        """Render the about page"""
        # Apply modern styles
        from ui_components import apply_modern_styles
        import base64
        import os

        # Function to load image as base64
        def get_image_as_base64(file_path):
            try:
                with open(file_path, "rb") as image_file:
                    encoded = base64.b64encode(image_file.read()).decode()
                    return f"data:image/jpeg;base64,{encoded}"
            except:
                return None

        # Get image path and convert to base64
        image_path = os.path.join(
    os.path.dirname(__file__),
    "assets",
     "124852522.jpeg")
        image_base64 = get_image_as_base64(image_path)

        apply_modern_styles()

        # Add Font Awesome icons and custom CSS
        st.markdown("""
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
            <style>
                .profile-section, .vision-section, .feature-card {
                    text-align: center;
                    padding: 2rem;
                    background: rgba(45, 45, 45, 0.9);
                    border-radius: 20px;
                    margin: 2rem auto;
                    max-width: 800px;
                }

                .profile-image {
                    width: 200px;
                    height: 200px;
                    border-radius: 50%;
                    margin: 0 auto 1.5rem;
                    display: block;
                    object-fit: cover;
                    border: 4px solid #4CAF50;
                }

                .profile-name {
                    font-size: 2.5rem;
                    color: white;
                    margin-bottom: 0.5rem;
                }

                .profile-title {
                    font-size: 1.2rem;
                    color: #4CAF50;
                    margin-bottom: 1.5rem;
                }

                .social-links {
                    display: flex;
                    justify-content: center;
                    gap: 1.5rem;
                    margin: 2rem 0;
                }

                .social-link {
                    font-size: 2rem;
                    color: #4CAF50;
                    transition: all 0.3s ease;
                    padding: 0.5rem;
                    border-radius: 50%;
                    background: rgba(76, 175, 80, 0.1);
                    width: 60px;
                    height: 60px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    text-decoration: none;
                }

                .social-link:hover {
                    transform: translateY(-5px);
                    background: #4CAF50;
                    color: white;
                    box-shadow: 0 5px 15px rgba(76, 175, 80, 0.3);
                }

                .bio-text {
                    color: #ddd;
                    line-height: 1.8;
                    font-size: 1.1rem;
                    margin-top: 2rem;
                    text-align: left;
                }

                .vision-text {
                    color: #ddd;
                    line-height: 1.8;
                    font-size: 1.1rem;
                    font-style: italic;
                    margin: 1.5rem 0;
                    text-align: left;
                }

                .vision-icon {
                    font-size: 2.5rem;
                    color: #4CAF50;
                    margin-bottom: 1rem;
                }

                .vision-title {
                    font-size: 2rem;
                    color: white;
                    margin-bottom: 1rem;
                }

                .features-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 2rem;
                    margin: 2rem auto;
                    max-width: 1200px;
                }

                .feature-card {
                    padding: 2rem;
                    margin: 0;
                }

                .feature-icon {
                    font-size: 2.5rem;
                    color: #4CAF50;
                    margin-bottom: 1rem;
                }

                .feature-title {
                    font-size: 1.5rem;
                    color: white;
                    margin: 1rem 0;
                }

                .feature-description {
                    color: #ddd;
                    line-height: 1.6;
                }
            </style>
        """, unsafe_allow_html=True)

        # Hero Section
        st.markdown("""
            <div class="hero-section">
                <h1 class="hero-title">About Smart Resume AI</h1>
                <p class="hero-subtitle">A powerful AI-driven platform for optimizing your resume</p>
            </div>
        """, unsafe_allow_html=True)

        # Profile Section
        # st.markdown(f"""
        #     <div class="profile-section">
        #         # <img src="{image_base64 if image_base64 else 'https://avatars.githubusercontent.com/Hunterdii'}"
        #         #      alt="Het Patel"
        #         #      class="profile-image"
        #         #      onerror="this.onerror=null; this.src='https://avatars.githubusercontent.com/Hunterdii';">
        #         <h2 class="profile-name">Ashutosh Garg</h2>
        #         <p class="profile-title">Full Stack Developer & AI/ML Enthusiast</p>
        #         <div class="social-links">
        #             <a href="https://github.com/Hunterdii" class="social-link" target="_blank">
        #                 <i class="fab fa-github"></i>
        #             </a>
        #             <a href="https://www.linkedin.com/in/patel-hetkumar-sandipbhai-8b110525a/" class="social-link" target="_blank">
        #                 <i class="fab fa-linkedin"></i>
        #             </a>
        #             <a href="mailto:hunterdii9879@gmail.com" class="social-link" target="_blank">
        #                 <i class="fas fa-envelope"></i>
        #             </a>
        #         </div>
        #         <p class="bio-text">
        #             Hello! I'm a passionate Full Stack Developer with expertise in AI and Machine Learning.
        #             I created Smart Resume AI to revolutionize how job seekers approach their career journey.
        #             With my background in both software development and AI, I've designed this platform to
        #             provide intelligent, data-driven insights for resume optimization.
        #         </p>
        #     </div>
        # """, unsafe_allow_html=True)




        # # Vision Section
        # st.markdown("""
        #     <div class="vision-section">
        #         <i class="fas fa-lightbulb vision-icon"></i>
        #         <h2 class="vision-title">Our Vision</h2>
        #         <p class="vision-text">
        #             "Smart Resume AI represents my vision of democratizing career advancement through technology.
        #             By combining cutting-edge AI with intuitive design, this platform empowers job seekers at
        #             every career stage to showcase their true potential and stand out in today's competitive job market."
        #         </p>
        #     </div>
        # """, unsafe_allow_html=True)

        # Features Section
        st.markdown("""
            <div class="features-grid">
                <div class="feature-card">
                    <i class="fas fa-robot feature-icon"></i>
                    <h3 class="feature-title">AI-Powered Analysis</h3>
                    <p class="feature-description">
                        Advanced AI algorithms provide detailed insights and suggestions to optimize your resume for maximum impact.
                    </p>
                </div>
                <div class="feature-card">
                    <i class="fas fa-chart-line feature-icon"></i>
                    <h3 class="feature-title">Data-Driven Insights</h3>
                    <p class="feature-description">
                        Make informed decisions with our analytics-based recommendations and industry insights.
                    </p>
                </div>
                <div class="feature-card">
                    <i class="fas fa-shield-alt feature-icon"></i>
                    <h3 class="feature-title">Privacy First</h3>
                    <p class="feature-description">
                        Your data security is our priority. We ensure your information is always protected and private.
                    </p>
                </div>
            </div>
            <div style="text-align: center; margin: 3rem 0;">
                <a href="?page=analyzer" class="cta-button">
                    Start Your Journey
                    <i class="fas fa-arrow-right" style="margin-left: 10px;"></i>
                </a>
            </div>
        """, unsafe_allow_html=True)

        st.toast("Check out these repositories: [Iriswise](https://github.com/Hunterdii/Iriswise)", icon="ℹ️")

    def render_analyzer(self):
        """Render the resume analyzer page"""
        apply_modern_styles()

        # Page Header
        page_header(
            "Resume Analyzer",
            "Get instant AI-powered feedback to optimize your resume"
        )

        # Create tabs for Normal Analyzer, AI Analyzer, Interview Prep, and Mock Interview
        analyzer_tabs = st.tabs(["Standard Analyzer", "AI Analyzer", "💡 Interview Prep", "🎙️ Mock Interview"])

        with analyzer_tabs[0]:
            # Job Role Selection
            categories = list(self.job_roles.keys())
            selected_category = st.selectbox(
    "Job Category", categories, key="standard_category")

            roles = list(self.job_roles[selected_category].keys())
            selected_role = st.selectbox(
    "Specific Role", roles, key="standard_role")

            role_info = self.job_roles[selected_category][selected_role]

            # Display role information
            st.markdown(f"""
            <div style='background-color: #1e1e1e; padding: 20px; border-radius: 10px; margin: 10px 0;'>
                <h3>{selected_role}</h3>
                <p>{role_info['description']}</p>
                <h4>Required Skills:</h4>
                <p>{', '.join(role_info['required_skills'])}</p>
            </div>
            """, unsafe_allow_html=True)

            # File Upload
            uploaded_file = st.file_uploader(
    "Upload your resume", type=[
        'pdf', 'docx'], key="standard_file")

            if not uploaded_file:
                # Display empty state with a prominent upload button
                st.markdown(
                    self.render_empty_state(
                    "fas fa-cloud-upload-alt",
                    "Upload your resume to get started with standard analysis"
                    ),
                    unsafe_allow_html=True
                )
                # Add a prominent upload button
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    st.markdown("""
                    <style>
                    .upload-button {
                        background: linear-gradient(90deg, #4b6cb7, #182848);
                        color: white;
                        border: none;
                        border-radius: 10px;
                        padding: 15px 25px;
                        font-size: 18px;
                        font-weight: bold;
                        cursor: pointer;
                        width: 100%;
                        text-align: center;
                        margin: 20px 0;
                        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
                        transition: all 0.3s ease;
                    }
                    .upload-button:hover {
                        transform: translateY(-3px);
                        box-shadow: 0 6px 15px rgba(0,0,0,0.3);
                    }

                    """, unsafe_allow_html=True)

            if uploaded_file:
                # Add a prominent analyze button
                analyze_standard = st.button("🔍 Analyze My Resume",
                                    type="primary",
                                    width='stretch',
                                    key="analyze_standard_button")

                if analyze_standard:
                    with st.spinner("Analyzing your document..."):
                        # Get file content
                        text = ""
                        try:
                            if uploaded_file.type == "application/pdf":
                                try:
                                    text = self.analyzer.extract_text_from_pdf(uploaded_file)
                                except Exception as pdf_error:
                                    st.error(f"PDF extraction failed: {str(pdf_error)}")
                                    st.info("Trying alternative PDF extraction method...")
                                    # Try AI analyzer as backup
                                    try:
                                        text = self.ai_analyzer.extract_text_from_pdf(uploaded_file)
                                    except Exception as backup_error:
                                        st.error(f"All PDF extraction methods failed: {str(backup_error)}")
                                        return
                            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                                try:
                                    text = self.analyzer.extract_text_from_docx(uploaded_file)
                                except Exception as docx_error:
                                    st.error(f"DOCX extraction failed: {str(docx_error)}")
                                    # Try AI analyzer as backup
                                    try:
                                        text = self.ai_analyzer.extract_text_from_docx(uploaded_file)
                                    except Exception as backup_error:
                                        st.error(f"All DOCX extraction methods failed: {str(backup_error)}")
                                        return
                            else:
                                text = uploaded_file.getvalue().decode()
                                
                            if not text or text.strip() == "":
                                st.error("Could not extract any text from the uploaded file. Please try a different file.")
                                return
                        except Exception as e:
                            st.error(f"Error reading file: {str(e)}")
                            return

                        # Analyze the document
                        analysis = self.analyzer.analyze_resume({'raw_text': text}, role_info)
                        
                        # Check if analysis returned an error
                        if 'error' in analysis:
                            st.error(analysis['error'])
                            return

                        # Show snowflake effect
                        # st.snow()

                        # Save resume data to database
                        resume_data = {
                            'personal_info': {
                                'full_name': analysis.get('name', 'Unknown Candidate'),
                                'email': analysis.get('email', 'No Email'),
                                'phone': analysis.get('phone', ''),
                                'location': '',
                                'linkedin': analysis.get('linkedin', ''),
                                'github': analysis.get('github', ''),
                                'portfolio': analysis.get('portfolio', '')
                            },
                            'summary': analysis.get('summary', ''),
                            'target_role': selected_role,
                            'target_category': selected_category,
                            'education': analysis.get('education', []),
                            'experience': analysis.get('experience', []),
                            'projects': analysis.get('projects', []),
                            'skills': analysis.get('skills', []),
                            'template': ''
                        }
                        
                        # Store in session state for Job Scraper auto-filling
                        st.session_state.candidate_profile = resume_data['personal_info']
                        st.session_state.candidate_profile['skills'] = resume_data['skills']
                        st.session_state.candidate_profile['experience_summary'] = resume_data['summary']

                        # Save to database
                        try:
                            resume_id = save_resume_data(resume_data)

                            # Save analysis data
                            analysis_data = {
                                'resume_id': resume_id,
                                'ats_score': analysis['ats_score'],
                                'keyword_match_score': analysis['keyword_match']['score'],
                                'format_score': analysis['format_score'],
                                'section_score': analysis['section_score'],
                                'missing_skills': ','.join(analysis['keyword_match']['missing_skills']),
                                'recommendations': ','.join(analysis['suggestions'])
                            }
                            save_analysis_data(resume_id, analysis_data)
                            st.success("Resume data saved successfully!")
                        except Exception as e:
                            st.error(f"Error saving to database: {str(e)}")
                            print(f"Database error: {e}")

                        # Show results based on document type
                        if analysis.get('document_type') != 'resume':
                            st.error(f"⚠️ This appears to be a {analysis['document_type']} document, not a resume!")
                            st.warning(
                                "Please upload a proper resume for ATS analysis.")
                                       # Display results in a modern card layout
                    col_res1, col_res2 = st.columns(2)

                    with col_res1:
                        # ATS Score Card with circular progress
                        st.markdown(f"""
                        <div class="glass-card" style="text-align: center; padding: 2.5rem;">
                            <h2 style="color: var(--text-main); margin-bottom: 2rem;">ATS Score</h2>
                            <div style="position: relative; width: 200px; height: 200px; margin: 0 auto; display: flex; align-items: center; justify-content: center;">
                                <svg viewBox="0 0 100 100" style="width: 100%; height: 100%; transform: rotate(-90deg);">
                                    <circle cx="50" cy="50" r="45" fill="none" stroke="var(--border-glass)" stroke-width="8" />
                                    <circle cx="50" cy="50" r="45" fill="none" stroke="url(#ats-grad)" stroke-width="8" 
                                            stroke-dasharray="282.7" stroke-dashoffset="{282.7 * (1 - analysis['ats_score']/100)}" 
                                            style="transition: stroke-dashoffset 1.5s ease-out;" />
                                    <defs>
                                        <linearGradient id="ats-grad" x1="0%" y1="0%" x2="100%" y2="0%">
                                            <stop offset="0%" style="stop-color:var(--primary);stop-opacity:1" />
                                            <stop offset="100%" style="stop-color:var(--primary-alt);stop-opacity:1" />
                                        </linearGradient>
                                    </defs>
                                </svg>
                                <div style="position: absolute; font-size: 3rem; font-weight: 800; color: var(--primary);">
                                    {analysis['ats_score']}<span style="font-size: 1.2rem;">%</span>
                                </div>
                            </div>
                            <div style="margin-top: 1.5rem; padding: 0.5rem 1.5rem; background: rgba(0, 242, 254, 0.1); border-radius: 50px; display: inline-block;">
                                <span style="font-size: 1.1rem; color: var(--primary); font-weight: 700;">
                                    {'EXCELLENT' if analysis['ats_score'] >= 80 else 'GOOD' if analysis['ats_score'] >= 60 else 'NEEDS WORK'}
                                </span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)

                        # self.display_analysis_results(analysis_results)

                        # Skills Match Card
                        st.markdown("""
                        <div class="glass-card" style="margin-top: 1.5rem;">
                            <h3 style="color: var(--text-main);"><i class="fas fa-tags" style="color: var(--primary); margin-right: 10px;"></i> Skills Match</h3>
                        """, unsafe_allow_html=True)

                        match_score = int(analysis.get('keyword_match', {}).get('score', 0))
                        progress_bar(match_score, "Keyword Alignment")

                        if analysis['keyword_match']['missing_skills']:
                            st.markdown('<p style="color: var(--error); font-weight: 600; margin-top: 1rem;">Missing Critical Skills:</p>', unsafe_allow_html=True)
                            skills_html = "".join([f'<span style="background: rgba(239, 68, 68, 0.1); color: var(--error); padding: 4px 12px; border-radius: 50px; font-size: 0.8rem; margin: 4px; display: inline-block; border: 1px solid rgba(239, 68, 68, 0.2);">{s}</span>' for s in analysis['keyword_match']['missing_skills']])
                            st.markdown(f'<div>{skills_html}</div>', unsafe_allow_html=True)

                        st.markdown("</div>", unsafe_allow_html=True)

                    with col_res2:
                        # Format Score Card
                        st.markdown("""
                        <div class="glass-card">
                            <h3 style="color: var(--text-main);"><i class="fas fa-tasks" style="color: var(--primary); margin-right: 10px;"></i> Format Analysis</h3>
                        """, unsafe_allow_html=True)

                        fmt_score = int(analysis.get('format_score', 0))
                        sec_score = int(analysis.get('section_score', 0))
                        
                        progress_bar(fmt_score, "Document Structure")
                        progress_bar(sec_score, "Section Presence")

                        st.markdown("</div>", unsafe_allow_html=True)

                        # Suggestions Card with improved UI
                        st.markdown("""
                        <div class="feature-card">
                            <h2>📋 Resume Improvement Suggestions</h2>
                        """, unsafe_allow_html=True)

                            # Contact Section
                        if analysis.get('contact_suggestions'):
                                st.markdown("""
                                <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                                    <h3 style='color: #4CAF50; margin-bottom: 10px;'>📞 Contact Information</h3>
                                    <ul style='list-style-type: none; padding-left: 0;'>
                                """, unsafe_allow_html=True)
                                for suggestion in analysis.get(
                                    'contact_suggestions', []):
                                    st.markdown(
    f"<li style='margin-bottom: 8px;'>✓ {suggestion}</li>",
     unsafe_allow_html=True)
                                st.markdown(
    "</ul></div>", unsafe_allow_html=True)

                            # Summary Section
                        if analysis.get('summary_suggestions'):
                                st.markdown("""
                                <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                                    <h3 style='color: #4CAF50; margin-bottom: 10px;'>📝 Professional Summary</h3>
                                    <ul style='list-style-type: none; padding-left: 0;'>
                                """, unsafe_allow_html=True)
                                for suggestion in analysis.get(
                                    'summary_suggestions', []):
                                    st.markdown(
    f"<li style='margin-bottom: 8px;'>✓ {suggestion}</li>",
     unsafe_allow_html=True)
                                st.markdown(
    "</ul></div>", unsafe_allow_html=True)

                            # Skills Section
                        if analysis.get(
                            'skills_suggestions') or analysis['keyword_match']['missing_skills']:
                                st.markdown("""
                                <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                                    <h3 style='color: #4CAF50; margin-bottom: 10px;'>🎯 Skills</h3>
                                    <ul style='list-style-type: none; padding-left: 0;'>
                                """, unsafe_allow_html=True)
                                for suggestion in analysis.get(
                                    'skills_suggestions', []):
                                    st.markdown(
    f"<li style='margin-bottom: 8px;'>✓ {suggestion}</li>",
     unsafe_allow_html=True)
                                if analysis['keyword_match']['missing_skills']:
                                    st.markdown(
    "<li style='margin-bottom: 8px;'>✓ Consider adding these relevant skills:</li>",
     unsafe_allow_html=True)
                                    for skill in analysis['keyword_match']['missing_skills']:
                                        st.markdown(
    f"<li style='margin-left: 20px; margin-bottom: 4px;'>• {skill}</li>",
     unsafe_allow_html=True)
                                st.markdown(
    "</ul></div>", unsafe_allow_html=True)

                            # Experience Section
                        if analysis.get('experience_suggestions'):
                                st.markdown("""
                                <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                                    <h3 style='color: #4CAF50; margin-bottom: 10px;'>💼 Work Experience</h3>
                                    <ul style='list-style-type: none; padding-left: 0;'>
                                """, unsafe_allow_html=True)
                                for suggestion in analysis.get(
                                    'experience_suggestions', []):
                                    st.markdown(
    f"<li style='margin-bottom: 8px;'>✓ {suggestion}</li>",
     unsafe_allow_html=True)
                                st.markdown(
    "</ul></div>", unsafe_allow_html=True)

                            # Education Section
                        if analysis.get('education_suggestions'):
                                st.markdown("""
                                <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                                    <h3 style='color: #4CAF50; margin-bottom: 10px;'>🎓 Education</h3>
                                    <ul style='list-style-type: none; padding-left: 0;'>
                                """, unsafe_allow_html=True)
                                for suggestion in analysis.get(
                                    'education_suggestions', []):
                                    st.markdown(
    f"<li style='margin-bottom: 8px;'>✓ {suggestion}</li>",
     unsafe_allow_html=True)
                                st.markdown(
    "</ul></div>", unsafe_allow_html=True)

                            # General Formatting Suggestions
                        if analysis.get('format_suggestions'):
                                st.markdown("""
                                <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                                    <h3 style='color: #4CAF50; margin-bottom: 10px;'>📄 Formatting</h3>
                                    <ul style='list-style-type: none; padding-left: 0;'>
                                """, unsafe_allow_html=True)
                                for suggestion in analysis.get(
                                    'format_suggestions', []):
                                    st.markdown(
    f"<li style='margin-bottom: 8px;'>✓ {suggestion}</li>",
     unsafe_allow_html=True)
                                st.markdown(
    "</ul></div>", unsafe_allow_html=True)

                        st.markdown("</div>", unsafe_allow_html=True)

                        # Course Recommendations
                    st.markdown("""
                        <div class="feature-card">
                            <h2>📚 Recommended Courses</h2>
                        """, unsafe_allow_html=True)

                        # Get courses based on role and category
                    courses = get_courses_for_role(selected_role)
                    if not courses:
                            category = get_category_for_role(selected_role)
                            courses = COURSES_BY_CATEGORY.get(
                                category, {}).get(selected_role, [])

                        # Display courses in a grid
                    cols = st.columns(2)
                    for i, course in enumerate(
                        courses[:6]):  # Show top 6 courses
                            with cols[i % 2]:
                                st.markdown(f"""
                                <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                                    <h4>{course[0]}</h4>
                                    <a href='{course[1]}' target='_blank'>View Course</a>
                                </div>
                                """, unsafe_allow_html=True)

                    st.markdown("</div>", unsafe_allow_html=True)

                        # Learning Resources
                    st.markdown("""
                        <div class="feature-card">
                            <h2>📺 Helpful Videos</h2>
                        """, unsafe_allow_html=True)

                    tab1, tab2 = st.tabs(["Resume Tips", "Interview Tips"])

                    with tab1:
                            # Resume Videos
                            for category, videos in RESUME_VIDEOS.items():
                                st.subheader(category)
                                cols = st.columns(2)
                                for i, video in enumerate(videos):
                                    with cols[i % 2]:
                                        st.video(video[1])

                    with tab2:
                            # Interview Videos
                            for category, videos in INTERVIEW_VIDEOS.items():
                                st.subheader(category)
                                cols = st.columns(2)
                                for i, video in enumerate(videos):
                                    with cols[i % 2]:
                                        st.video(video[1])
                            
                            st.markdown("---")
                            st.markdown("### 🤖 Level Up with AI")
                            if st.button(f"✨ Generate Real Interview Questions for {selected_role}", key="std_gen_qs"):
                                from utils.interview_fetcher import InterviewFetcher
                                fetcher = InterviewFetcher()
                                with st.spinner(f"Preparing interview questions for {selected_role}..."):
                                    questions, provider, context = fetcher.fetch_all("General", selected_role)
                                    if questions:
                                        st.session_state.std_questions = questions
                                        st.session_state.std_questions_context = context
                                    else:
                                        st.warning("Could not gather questions for this role at this time.")
                            
                            if 'std_questions' in st.session_state:
                                questions = st.session_state.std_questions
                                context = st.session_state.std_questions_context
                                st.info(f"**Tier:** {context.get('tier')} | **Domain:** {context.get('domain')}")
                                for q in questions:
                                    badge_color = "#f59e0b" if q['importance'] == 'Rare' else "#4CAF50"
                                    st.markdown(f"""
                                        <div style="background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid {badge_color};">
                                            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 5px;">
                                                <span style="background: {badge_color}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: bold;">{q['importance'].upper()}</span>
                                                <span style="color: #666; font-size: 0.8rem;">📍 Asked at: <b>{q['company']}</b></span>
                                            </div>
                                            <div style="font-size: 1rem; font-weight: 500; margin-bottom: 8px;">{q['question']}</div>
                                        </div>
                                    """, unsafe_allow_html=True)

                    st.markdown("</div>", unsafe_allow_html=True)

        with analyzer_tabs[1]:
            st.markdown("""
            <div style='background-color: #1e1e1e; padding: 20px; border-radius: 10px; margin: 10px 0;'>
                <h3>AI-Powered Resume Analysis</h3>
                <p>Get detailed insights from advanced AI models that analyze your resume and provide personalized recommendations.</p>
                <p><strong>Upload your resume to get AI-powered analysis and recommendations.</strong></p>
            </div>
            """, unsafe_allow_html=True)

            # AI Model Selection
            ai_model = st.selectbox(
                "Select AI Model",
                ["Google Gemini"],
                help="Choose the AI model to analyze your resume"
            )
             
            # Add job description input option
            use_custom_job_desc = st.checkbox("Use custom job description", value=False, 
                                             help="Enable this to provide a specific job description for more targeted analysis")
            
            custom_job_description = ""
            if use_custom_job_desc:
                custom_job_description = st.text_area(
                    "Paste the job description here",
                    height=200,
                    placeholder="Paste the full job description from the company here for more targeted analysis...",
                    help="Providing the actual job description will help the AI analyze your resume specifically for this position"
                )
                
                st.markdown("""
                <div style='background-color: #2e7d32; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                    <p><i class="fas fa-lightbulb"></i> <strong>Pro Tip:</strong> Including the actual job description significantly improves the accuracy of the analysis and provides more relevant recommendations tailored to the specific position.</p>
                </div>
                """, unsafe_allow_html=True)
             
                        # Add AI Analyzer Stats in an expander
            with st.expander("📊 AI Analyzer Statistics", expanded=False):
                try:
                    # Add a reset button for admin users
                    if st.session_state.get('is_admin', False):
                        if st.button(
    "🔄 Reset AI Analysis Statistics",
    type="secondary",
     key="reset_ai_stats_button_2"):
                            from config.database import reset_ai_analysis_stats
                            result = reset_ai_analysis_stats()
                            if result["success"]:
                                st.success(result["message"])
                            else:
                                st.error(result["message"])
                            # Refresh the page to show updated stats
                            st.experimental_rerun()

                    # Get detailed AI analysis statistics
                    from config.database import get_detailed_ai_analysis_stats
                    ai_stats = get_detailed_ai_analysis_stats()

                    if ai_stats["total_analyses"] > 0:
                        # Create a more visually appealing layout
                        st.markdown("""
                        <style>
                        .stats-card {
                            background: linear-gradient(135deg, #1e3c72, #2a5298);
                            border-radius: 10px;
                            padding: 15px;
                            margin-bottom: 15px;
                            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                            text-align: center;
                        }
                        .stats-value {
                            font-size: 28px;
                            font-weight: bold;
                            color: white;
                            margin: 10px 0;
                        }
                        .stats-label {
                            font-size: 14px;
                            color: rgba(255, 255, 255, 0.8);
                            text-transform: uppercase;
                            letter-spacing: 1px;
                        }
                        .score-card {
                            background: linear-gradient(135deg, #11998e, #38ef7d);
                            border-radius: 10px;
                            padding: 15px;
                            margin-bottom: 15px;
                            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                            text-align: center;
                        }
                        </style>
                        """, unsafe_allow_html=True)

                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.markdown(f"""
                            <div class="stats-card">
                                <div class="stats-label">Total AI Analyses</div>
                                <div class="stats-value">{ai_stats["total_analyses"]}</div>
                            </div>
                            """, unsafe_allow_html=True)

                        with col2:
                            # Determine color based on score
                            score_color = "#38ef7d" if ai_stats["average_score"] >= 80 else "#FFEB3B" if ai_stats[
                                "average_score"] >= 60 else "#FF5252"
                            st.markdown(f"""
                            <div class="stats-card" style="background: linear-gradient(135deg, #2c3e50, {score_color});">
                                <div class="stats-label">Average Resume Score</div>
                                <div class="stats-value">{ai_stats["average_score"]}/100</div>
                            </div>
                            """, unsafe_allow_html=True)

                        with col3:
                            # Create a gauge chart for average score
                            import plotly.graph_objects as go
                            fig = go.Figure(go.Indicator(
                                mode="gauge+number",
                                value=ai_stats["average_score"],
                                domain={'x': [0, 1], 'y': [0, 1]},
                                title={
    'text': "Score", 'font': {
        'size': 14, 'color': 'white'}},
                                gauge={
                                    'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "white"},
                                    'bar': {'color': "#38ef7d" if ai_stats["average_score"] >= 80 else "#FFEB3B" if ai_stats["average_score"] >= 60 else "#FF5252"},
                                    'bgcolor': "rgba(0,0,0,0)",
                                    'borderwidth': 2,
                                    'bordercolor': "white",
                                    'steps': [
                                        {'range': [
                                            0, 40], 'color': 'rgba(255, 82, 82, 0.3)'},
                                        {'range': [
                                            40, 70], 'color': 'rgba(255, 235, 59, 0.3)'},
                                        {'range': [
                                            70, 100], 'color': 'rgba(56, 239, 125, 0.3)'}
                                    ],
                                }
                            ))

                            fig.update_layout(
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                font={'color': "white"},
                                height=150,
                                margin=dict(l=10, r=10, t=30, b=10)
                            )

                            st.plotly_chart(fig, use_container_width=True)

                        # Display model usage with enhanced visualization
                        if ai_stats["model_usage"]:
                            st.markdown("### 🤖 Model Usage")
                            model_data = pd.DataFrame(ai_stats["model_usage"])

                            # Create a more colorful pie chart
                            import plotly.express as px
                            fig = px.pie(
                                model_data,
                                values="count",
                                names="model",
                                color_discrete_sequence=px.colors.qualitative.Bold,
                                hole=0.4
                            )

                            fig.update_traces(
                                textposition='inside',
                                textinfo='percent+label',
                                marker=dict(
    line=dict(
        color='#000000',
         width=1.5))
                            )

                            fig.update_layout(
                                margin=dict(l=20, r=20, t=30, b=20),
                                height=300,
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                font=dict(color="#ffffff", size=14),
                                legend=dict(
                                    orientation="h",
                                    yanchor="bottom",
                                    y=-0.1,
                                    xanchor="center",
                                    x=0.5
                                ),
                                title={
                                    'text': 'AI Model Distribution',
                                    'y': 0.95,
                                    'x': 0.5,
                                    'xanchor': 'center',
                                    'yanchor': 'top',
                                    'font': {'size': 18, 'color': 'white'}
                                }
                            )

                            st.plotly_chart(fig, use_container_width=True)

                        # Display top job roles with enhanced visualization
                        if ai_stats["top_job_roles"]:
                            st.markdown("### 🎯 Top Job Roles")
                            roles_data = pd.DataFrame(
                                ai_stats["top_job_roles"])

                            # Create a more colorful bar chart
                            fig = px.bar(
                                roles_data,
                                x="role",
                                y="count",
                                color="count",
                                color_continuous_scale=px.colors.sequential.Viridis,
                                labels={
    "role": "Job Role", "count": "Number of Analyses"}
                            )

                            fig.update_traces(
                                marker_line_width=1.5,
                                marker_line_color="white",
                                opacity=0.9
                            )

                            fig.update_layout(
                                margin=dict(l=20, r=20, t=50, b=30),
                                height=350,
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                font=dict(color="#ffffff", size=14),
                                title={
                                    'text': 'Most Analyzed Job Roles',
                                    'y': 0.95,
                                    'x': 0.5,
                                    'xanchor': 'center',
                                    'yanchor': 'top',
                                    'font': {'size': 18, 'color': 'white'}
                                },
                                xaxis=dict(
                                    title="",
                                    tickangle=-45,
                                    tickfont=dict(size=12)
                                ),
                                yaxis=dict(
                                    title="Number of Analyses",
                                    gridcolor="rgba(255, 255, 255, 0.1)"
                                ),
                                coloraxis_showscale=False
                            )

                            st.plotly_chart(fig, use_container_width=True)

                            # Add a timeline chart for analysis over time (mock
                            # data for now)
                            st.markdown("### 📈 Analysis Trend")
                            st.info(
                                "This is a conceptual visualization. To implement actual time-based analysis, additional data collection would be needed.")

                            # Create mock data for timeline
                            import datetime
                            import numpy as np

                            today = datetime.datetime.now()
                            dates = [
    (today -
    datetime.timedelta(
        days=i)).strftime('%Y-%m-%d') for i in range(7)]
                            dates.reverse()

                            # Generate some random data that sums to
                            # total_analyses
                            total = ai_stats["total_analyses"]
                            if total > 7:
                                values = np.random.dirichlet(
                                    np.ones(7)) * total
                                values = [round(v) for v in values]
                                # Adjust to make sure sum equals total
                                diff = total - sum(values)
                                values[-1] += diff
                            else:
                                values = [0] * 7
                                for i in range(total):
                                    values[-(i % 7) - 1] += 1

                            trend_data = pd.DataFrame({
                                'Date': dates,
                                'Analyses': values
                            })

                            fig = px.line(
                                trend_data,
                                x='Date',
                                y='Analyses',
                                markers=True,
                                line_shape='spline',
                                color_discrete_sequence=["#38ef7d"]
                            )

                            fig.update_traces(
                                line=dict(width=3),
                                marker=dict(
    size=8, line=dict(
        width=2, color='white'))
                            )

                            fig.update_layout(
                                margin=dict(l=20, r=20, t=50, b=30),
                                height=300,
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                font=dict(color="#ffffff", size=14),
                                title={
                                    'text': 'Analysis Activity (Last 7 Days)',
                                    'y': 0.95,
                                    'x': 0.5,
                                    'xanchor': 'center',
                                    'yanchor': 'top',
                                    'font': {'size': 18, 'color': 'white'}
                                },
                                xaxis=dict(
                                    title="",
                                    gridcolor="rgba(255, 255, 255, 0.1)"
                                ),
                                yaxis=dict(
                                    title="Number of Analyses",
                                    gridcolor="rgba(255, 255, 255, 0.1)"
                                )
                            )

                            st.plotly_chart(fig, use_container_width=True)

                        # Display score distribution if available
                        if ai_stats["score_distribution"]:
                            st.markdown("""
                            <h3 style='text-align: center; margin-bottom: 20px; background: linear-gradient(90deg, #4b6cb7, #182848); padding: 15px; border-radius: 10px; color: white; box-shadow: 0 4px 10px rgba(0,0,0,0.2);'>
                                📊 Score Distribution Analysis
                            </h3>
                            """, unsafe_allow_html=True)

                            score_data = pd.DataFrame(
                                ai_stats["score_distribution"])

                            # Create a more visually appealing bar chart for
                            # score distribution
                            fig = px.bar(
                                score_data,
                                x="range",
                                y="count",
                                color="range",
                                color_discrete_map={
                                    "0-20": "#FF5252",
                                    "21-40": "#FF7043",
                                    "41-60": "#FFEB3B",
                                    "61-80": "#8BC34A",
                                    "81-100": "#38ef7d"
                                },
                                labels={
    "range": "Score Range",
     "count": "Number of Resumes"},
                                text="count"  # Display count values on bars
                            )

                            fig.update_traces(
                                marker_line_width=2,
                                marker_line_color="white",
                                opacity=0.9,
                                textposition='outside',
                                textfont=dict(
    color="white", size=14, family="Arial, sans-serif"),
                                hovertemplate="<b>Score Range:</b> %{x}<br><b>Number of Resumes:</b> %{y}<extra></extra>"
                            )

                            # Add a gradient background to the chart
                            fig.update_layout(
                                margin=dict(l=20, r=20, t=50, b=30),
                                height=400,  # Increase height for better visibility
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                font=dict(
    color="#ffffff", size=14, family="Arial, sans-serif"),
                                # title={
                                #     # 'text': 'Resume Score Distribution',
                                #     'y': 0.95,
                                #     'x': 0.5,
                                #     'xanchor': 'center',
                                #     'yanchor': 'top',
                                #     'font': {'size': 22, 'color': 'white', 'family': 'Arial, sans-serif', 'weight': 'bold'}
                                # },
                                xaxis=dict(
                                    title=dict(
    text="Score Range", font=dict(
        size=16, color="white")),
                                    categoryorder="array",
                                    categoryarray=[
    "0-20", "21-40", "41-60", "61-80", "81-100"],
                                    tickfont=dict(size=14, color="white"),
                                    gridcolor="rgba(255, 255, 255, 0.1)"
                                ),
                                yaxis=dict(
                                    title=dict(
    text="Number of Resumes", font=dict(
        size=16, color="white")),
                                    tickfont=dict(size=14, color="white"),
                                    gridcolor="rgba(255, 255, 255, 0.1)",
                                    zeroline=False
                                ),
                                showlegend=False,
                                bargap=0.2,  # Adjust gap between bars
                                shapes=[
                                    # Add gradient background
                                    dict(
                                        type="rect",
                                        xref="paper",
                                        yref="paper",
                                        x0=0,
                                        y0=0,
                                        x1=1,
                                        y1=1,
                                        fillcolor="rgba(26, 26, 44, 0.5)",
                                        layer="below",
                                        line_width=0,
                                    )
                                ]
                            )

                            # Add annotations for insights
                            if len(score_data) > 0:
                                max_count_idx = score_data["count"].idxmax()
                                max_range = score_data.iloc[max_count_idx]["range"]
                                max_count = score_data.iloc[max_count_idx]["count"]

                                fig.add_annotation(
                                    x=0.5,
                                    y=1.12,
                                    xref="paper",
                                    yref="paper",
                                    text=f"Most resumes fall in the {max_range} score range",
                                    showarrow=False,
                                    font=dict(size=14, color="#FFEB3B"),
                                    bgcolor="rgba(0,0,0,0.5)",
                                    bordercolor="#FFEB3B",
                                    borderwidth=1,
                                    borderpad=4,
                                    opacity=0.8
                                )

                            # Display the chart in a styled container
                            st.markdown("""
                            <div style='background: linear-gradient(135deg, #1e3c72, #2a5298); padding: 20px; border-radius: 15px; margin: 10px 0; box-shadow: 0 5px 15px rgba(0,0,0,0.2);'>
                            """, unsafe_allow_html=True)

                            st.plotly_chart(fig, use_container_width=True)

                            # Add descriptive text below the chart
                            st.markdown("""
                            <p style='color: white; text-align: center; font-style: italic; margin-top: 10px;'>
                                This chart shows the distribution of resume scores across different ranges, helping identify common performance levels.
                            </p>
                            </div>
                            """, unsafe_allow_html=True)

                        # Display recent analyses if available
                        if ai_stats["recent_analyses"]:
                            st.markdown("""
                            <h3 style='text-align: center; margin-bottom: 20px; background: linear-gradient(90deg, #4b6cb7, #182848); padding: 15px; border-radius: 10px; color: white; box-shadow: 0 4px 10px rgba(0,0,0,0.2);'>
                                🕒 Recent Resume Analyses
                            </h3>
                            """, unsafe_allow_html=True)

                            # Create a more modern styled table for recent
                            # analyses
                            st.markdown("""
                            <style>
                            .modern-analyses-table {
                                width: 100%;
                                border-collapse: separate;
                                border-spacing: 0 8px;
                                margin-bottom: 20px;
                                font-family: 'Arial', sans-serif;
                            }
                            .modern-analyses-table th {
                                background: linear-gradient(135deg, #1e3c72, #2a5298);
                                color: white;
                                padding: 15px;
                                text-align: left;
                                font-weight: bold;
                                font-size: 14px;
                                text-transform: uppercase;
                                letter-spacing: 1px;
                                border-radius: 8px;
                            }
                            .modern-analyses-table td {
                                padding: 15px;
                                background-color: rgba(30, 30, 30, 0.7);
                                border-top: 1px solid rgba(255, 255, 255, 0.05);
                                border-bottom: 1px solid rgba(0, 0, 0, 0.2);
                                color: white;
                            }
                            .modern-analyses-table tr td:first-child {
                                border-top-left-radius: 8px;
                                border-bottom-left-radius: 8px;
                            }
                            .modern-analyses-table tr td:last-child {
                                border-top-right-radius: 8px;
                                border-bottom-right-radius: 8px;
                            }
                            .modern-analyses-table tr:hover td {
                                background-color: rgba(60, 60, 60, 0.7);
                                transform: translateY(-2px);
                                transition: all 0.2s ease;
                                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
                            }
                            .model-badge {
                                display: inline-block;
                                padding: 6px 12px;
                                border-radius: 20px;
                                font-weight: bold;
                                text-align: center;
                                font-size: 12px;
                                letter-spacing: 0.5px;
                                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
                            }
                            .model-gemini {
                                background: linear-gradient(135deg, #4e54c8, #8f94fb);
                                color: white;
                            }
                            .model-claude {
                                background: linear-gradient(135deg, #834d9b, #d04ed6);
                                color: white;
                            }
                            .score-pill {
                                display: inline-block;
                                padding: 8px 15px;
                                border-radius: 20px;
                                font-weight: bold;
                                text-align: center;
                                min-width: 70px;
                                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
                            }
                            .score-high {
                                background: linear-gradient(135deg, #11998e, #38ef7d);
                                color: white;
                            }
                            .score-medium {
                                background: linear-gradient(135deg, #f2994a, #f2c94c);
                                color: white;
                            }
                            .score-low {
                                background: linear-gradient(135deg, #cb2d3e, #ef473a);
                                color: white;
                            }
                            .date-badge {
                                display: inline-block;
                                padding: 6px 12px;
                                border-radius: 20px;
                                background-color: rgba(255, 255, 255, 0.1);
                                color: #e0e0e0;
                                font-size: 12px;
                            }
                            .role-badge {
                                display: inline-block;
                                padding: 6px 12px;
                                border-radius: 8px;
                                background-color: rgba(33, 150, 243, 0.2);
                                color: #90caf9;
                                font-size: 13px;
                                max-width: 200px;
                                white-space: nowrap;
                                overflow: hidden;
                                text-overflow: ellipsis;
                            }
                            </style>

                            <div style='background: linear-gradient(135deg, #1e3c72, #2a5298); padding: 20px; border-radius: 15px; margin: 10px 0; box-shadow: 0 5px 15px rgba(0,0,0,0.2);'>
                            <table class="modern-analyses-table">
                                <tr>
                                    <th>AI Model</th>
                                    <th>Score</th>
                                    <th>Job Role</th>
                                    <th>Date</th>
                                </tr>
                            """, unsafe_allow_html=True)

                            for analysis in ai_stats["recent_analyses"]:
                                score = analysis["score"]
                                score_class = "score-high" if score >= 80 else "score-medium" if score >= 60 else "score-low"

                                # Determine model class
                                model_name = analysis["model"]
                                model_class = "model-gemini" if "Gemini" in model_name else "model-claude" if "Claude" in model_name else ""

                                # Format the date
                                try:
                                    from datetime import datetime
                                    date_obj = datetime.strptime(
                                        analysis["date"], "%Y-%m-%d %H:%M:%S")
                                    formatted_date = date_obj.strftime(
                                        "%b %d, %Y")
                                except:
                                    formatted_date = analysis["date"]

                                st.markdown(f"""
                                <tr>
                                    <td><div class="model-badge {model_class}">{model_name}</div></td>
                                    <td><div class="score-pill {score_class}">{score}/100</div></td>
                                    <td><div class="role-badge">{analysis["job_role"]}</div></td>
                                    <td><div class="date-badge">{formatted_date}</div></td>
                                </tr>
                                """, unsafe_allow_html=True)

                            st.markdown("""
                            </table>

                            <p style='color: white; text-align: center; font-style: italic; margin-top: 15px;'>
                                These are the most recent resume analyses performed by our AI models.
                            </p>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info(
                            "No AI analysis data available yet. Upload and analyze resumes to see statistics here.")
                except Exception as e:
                    st.error(f"Error loading AI analysis statistics: {str(e)}")

            # Job Role Selection for AI Analysis
            categories = list(self.job_roles.keys())
            selected_category = st.selectbox(
    "Job Category", categories, key="ai_category")

            roles = list(self.job_roles[selected_category].keys())
            selected_role = st.selectbox("Specific Role", roles, key="ai_role")

            role_info = self.job_roles[selected_category][selected_role]

            # Display role information
            st.markdown(f"""
            <div style='background-color: #1e1e1e; padding: 20px; border-radius: 10px; margin: 10px 0;'>
                <h3>{selected_role}</h3>
                <p>{role_info['description']}</p>
                <h4>Required Skills:</h4>
                <p>{', '.join(role_info['required_skills'])}</p>
            </div>
            """, unsafe_allow_html=True)

            # File Upload for AI Analysis
            uploaded_file = st.file_uploader(
    "Upload your resume", type=[
        'pdf', 'docx'], key="ai_file")

            if not uploaded_file:
            # Display empty state with a prominent upload button
                st.markdown(
                self.render_empty_state(
            "fas fa-robot",
                        "Upload your resume to get AI-powered analysis and recommendations"
        ),
        unsafe_allow_html=True
    )
            else:
                # Add a prominent analyze button
                analyze_ai = st.button("🤖 Analyze with AI",
                                type="primary",
                                width='stretch',
                                key="analyze_ai_button")

                if analyze_ai:
                    with st.spinner(f"Analyzing your resume with {ai_model}..."):
                        # Get file content
                        text = ""
                        try:
                            if uploaded_file.type == "application/pdf":
                                text = self.analyzer.extract_text_from_pdf(
                                    uploaded_file)
                            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                                text = self.analyzer.extract_text_from_docx(
                                    uploaded_file)
                            else:
                                text = uploaded_file.getvalue().decode()
                        except Exception as e:
                            st.error(f"Error reading file: {str(e)}")
                            st.stop()

                        # Analyze with AI
                        try:
                            # Show a loading animation
                            with st.spinner("🧠 AI is analyzing your resume..."):
                                ai_progress = st.progress(0)
                                
                                # Get the selected model
                                selected_model = "Google Gemini"
                                
                                # Update progress
                                ai_progress.progress(10)
                                
                                # Extract text from the resume
                                analyzer = AIResumeAnalyzer()
                                if uploaded_file.type == "application/pdf":
                                    resume_text = analyzer.extract_text_from_pdf(
                                        uploaded_file)
                                elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                                    resume_text = analyzer.extract_text_from_docx(
                                        uploaded_file)
                                else:
                                    # For text files or other formats
                                    resume_text = uploaded_file.getvalue().decode('utf-8')
                                
                                # Initialize the AI analyzer (moved after text extraction)
                                ai_progress.progress(30)
                                
                                # Get the job role
                                job_role = selected_role if selected_role else "Not specified"
                                
                                # Update progress
                                ai_progress.progress(50)
                                
                                # Analyze the resume with LLM Orchestrator
                                if use_custom_job_desc and custom_job_description:
                                    # Use custom job description for analysis
                                    analysis_result = analyzer.analyze_resume(
                                        resume_text, job_role=job_role, job_description=custom_job_description)
                                    # Show that custom job description was used
                                    st.session_state['used_custom_job_desc'] = True
                                else:
                                    # Use standard role-based analysis
                                    analysis_result = analyzer.analyze_resume(
                                        resume_text, job_role=job_role)
                                    st.session_state['used_custom_job_desc'] = False

                                
                                # Update progress
                                ai_progress.progress(80)
                                
                                # Save the analysis to the database
                                if analysis_result and "error" not in analysis_result:
                                    # Extract the resume score
                                    resume_score = analysis_result.get(
                                        "resume_score", 0)
                                    
                                    # Save to database
                                    save_ai_analysis_data(
                                        None,  # No user_id needed
                                        {
                                            "model_used": selected_model,
                                            "resume_score": resume_score,
                                            "job_role": job_role
                                        }
                                    )
                                    
                                    # Sync candidate to Recruiter Hub
                                    try:
                                        # Use standard parser to extract personal details
                                        parsed_data = self.analyzer.analyze_resume({'raw_text': resume_text}, role_info)
                                        if parsed_data and 'error' not in parsed_data:
                                            resume_data = {
                                                'personal_info': {
                                                    'full_name': parsed_data.get('name', 'AI User'),
                                                    'email': parsed_data.get('email', ''),
                                                    'phone': parsed_data.get('phone', ''),
                                                    'location': '',
                                                    'linkedin': parsed_data.get('linkedin', ''),
                                                    'github': parsed_data.get('github', ''),
                                                    'portfolio': parsed_data.get('portfolio', '')
                                                },
                                                'summary': parsed_data.get('summary', ''),
                                                'target_role': job_role,
                                                'target_category': selected_category,
                                                'education': parsed_data.get('education', []),
                                                'experience': parsed_data.get('experience', []),
                                                'projects': parsed_data.get('projects', []),
                                                'skills': parsed_data.get('skills', []),
                                                'template': 'AI-Analyzed'
                                            }
                                            resume_id = save_resume_data(resume_data)
                                            if resume_id:
                                                ats_score = analysis_result.get("ats_score", resume_score)
                                                hub_analysis_data = {
                                                    'resume_id': resume_id,
                                                    'ats_score': ats_score,
                                                    'keyword_match_score': resume_score,
                                                    'format_score': resume_score,
                                                    'section_score': resume_score,
                                                    'missing_skills': '',
                                                    'recommendations': 'Reviewed via AI Analyzer'
                                                }
                                                save_analysis_data(resume_id, hub_analysis_data)
                                                
                                                # Store in session state for Job Scraper auto-filling
                                                st.session_state.candidate_profile = resume_data['personal_info']
                                                st.session_state.candidate_profile['skills'] = resume_data['skills']
                                                st.session_state.candidate_profile['experience_summary'] = resume_data['summary']
                                    except Exception as db_err:
                                        print(f"Failed to sync with Recruiter Hub: {db_err}")

                                # show snowflake effect
                                st.snow()

                                # Complete the progress
                                ai_progress.progress(100)
                                
                                # Display the analysis result
                                if analysis_result and "error" not in analysis_result:
                                    st.success("✅ Analysis complete!")
                                    
                                    # Extract data from the analysis
                                    full_response = analysis_result.get(
                                        "analysis", "")
                                    resume_score = analysis_result.get(
                                        "resume_score", 0)
                                    ats_score = analysis_result.get(
                                        "ats_score", 0)
                                    model_used = analysis_result.get(
                                        "model_used", selected_model)
                                    
                                    # Store the full response in session state for download
                                    st.session_state['full_analysis'] = full_response
                                    
                                    # Display the analysis in a nice format
                                    st.markdown("## Full Analysis Report")
                                    
                                    # Get current date
                                    from datetime import datetime
                                    current_date = datetime.now().strftime("%B %d, %Y")
                                    
                                    # Create a modern styled header for the report
                                    st.markdown(f"""
                                    <div style="background-color: #262730; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                                        <h2 style="color: #ffffff; margin-bottom: 10px;">AI Resume Analysis Report</h2>
                                        <div style="display: flex; flex-wrap: wrap; gap: 20px;">
                                            <div style="flex: 1; min-width: 200px;">
                                                <p style="color: #ffffff;"><strong>Job Role:</strong> {job_role if job_role else "Not specified"}</p>
                                                <p style="color: #ffffff;"><strong>Analysis Date:</strong> {current_date}</p>                                                                                                                                        </div>
                                            <div style="flex: 1; min-width: 200px;">
                                                <p style="color: #ffffff;"><strong>AI Model:</strong> {model_used}</p>
                                                <p style="color: #ffffff;"><strong>Overall Score:</strong> {resume_score}/100 - {"Excellent" if resume_score >= 80 else "Good" if resume_score >= 60 else "Needs Improvement"}</p>
                                                {f'<p style="color: #4CAF50;"><strong>✓ Custom Job Description Used</strong></p>' if st.session_state.get('used_custom_job_desc', False) else ''}
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    # Add gauge charts for scores
                                    import plotly.graph_objects as go
                                    
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        # Resume Score Gauge
                                        fig1 = go.Figure(go.Indicator(
                                            mode="gauge+number",
                                            value=resume_score,
                                            domain={'x': [0, 1], 'y': [0, 1]},
                                            title={'text': "Resume Score", 'font': {'size': 16}},
                                            gauge={
                                                'axis': {'range': [0, 100], 'tickwidth': 1},
                                                'bar': {'color': "#4CAF50" if resume_score >= 80 else "#FFA500" if resume_score >= 60 else "#FF4444"},
                                                'bgcolor': "white",
                                                'borderwidth': 2,
                                                'bordercolor': "gray",
                                                'steps': [
                                                    {'range': [0, 40], 'color': 'rgba(255, 68, 68, 0.2)'},
                                                    {'range': [40, 60], 'color': 'rgba(255, 165, 0, 0.2)'},
                                                    {'range': [60, 80], 'color': 'rgba(255, 214, 0, 0.2)'},
                                                    {'range': [80, 100], 'color': 'rgba(76, 175, 80, 0.2)'}
                                                ],
                                                'threshold': {
                                                    'line': {'color': "red", 'width': 4},
                                                    'thickness': 0.75,
                                                    'value': 60
                                                }
                                            }
                                        ))
                                        
                                        fig1.update_layout(
                                            height=250,
                                            margin=dict(l=20, r=20, t=50, b=20),
                                        )
                                        
                                        st.plotly_chart(fig1, use_container_width=True)
                                        
                                        # status = "Excellent" if resume_score >= 80 else "Good" if resume_score >= 60 else "Needs Improvement"
                                        st.markdown(f"""
                                            <div style="text-align: center; margin-top: 10px;">
                                                <span style="background: rgba(0, 242, 254, 0.1); color: var(--primary); padding: 5px 15px; border-radius: 50px; font-weight: 700; font-size: 0.9rem; border: 1px solid rgba(0, 242, 254, 0.2);">
                                                    {'EXCELLENT' if resume_score >= 80 else 'GOOD' if resume_score >= 60 else 'NEEDS WORK'}
                                                </span>
                                            </div>
                                        """, unsafe_allow_html=True)
                                    
                                    with col2:
                                        # ATS Score Gauge
                                        fig2 = go.Figure(go.Indicator(
                                            mode="gauge+number",
                                            value=ats_score,
                                            domain={'x': [0, 1], 'y': [0, 1]},
                                            title={'text': "ATS Optimization Score", 'font': {'size': 16, 'color': '#f8fafc'}},
                                            gauge={
                                                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': '#94a3b8'},
                                                'bar': {'color': "#00f2fe"},
                                                'bgcolor': "rgba(255,255,255,0.05)",
                                                'borderwidth': 0,
                                                'steps': [
                                                    {'range': [0, 100], 'color': 'rgba(255,255,255,0.02)'}
                                                ],
                                                'threshold': {
                                                    'line': {'color': "var(--primary)", 'width': 4},
                                                    'thickness': 0.75,
                                                    'value': 100
                                                }
                                            }
                                        ))
                                        
                                        fig2.update_layout(
                                            height=250,
                                            paper_bgcolor='rgba(0,0,0,0)',
                                            plot_bgcolor='rgba(0,0,0,0)',
                                            font={'color': '#f8fafc'},
                                            margin=dict(l=20, r=20, t=50, b=20),
                                        )
                                        
                                        st.plotly_chart(fig2, use_container_width=True)
                                        
                                        st.markdown(f"""
                                            <div style="text-align: center; margin-top: 10px;">
                                                <span style="background: rgba(79, 209, 197, 0.1); color: #4fd1c5; padding: 5px 15px; border-radius: 50px; font-weight: 700; font-size: 0.9rem; border: 1px solid rgba(79, 209, 197, 0.2);">
                                                    {'OPTIMIZED' if ats_score >= 80 else 'AVERAGE' if ats_score >= 60 else 'POOR'}
                                                </span>
                                            </div>
                                        """, unsafe_allow_html=True)

                                    # Add Job Description Match Score if custom job description was used
                                    if st.session_state.get('used_custom_job_desc', False) and custom_job_description:
                                        # Extract job match score from analysis result or calculate it
                                        job_match_score = analysis_result.get("job_match_score", 0)
                                        if not job_match_score and "job_match" in analysis_result:
                                            job_match_score = analysis_result["job_match"].get("score", 0)
                                        
                                        # If we have a job match score, display it
                                        if job_match_score:
                                            st.markdown("""
                                            <h3 style="background: linear-gradient(90deg, #4d7c0f, #84cc16); color: white; padding: 10px; border-radius: 5px; margin-top: 20px;">
                                                <i class="fas fa-handshake"></i> Job Description Match Analysis
                                            </h3>
                                            """, unsafe_allow_html=True)
                                            
                                            col1, col2 = st.columns(2)
                                            
                                            with col1:
                                                # Job Match Score Gauge
                                                fig3 = go.Figure(go.Indicator(
                                                    mode="gauge+number",
                                                    value=job_match_score,
                                                    domain={'x': [0, 1], 'y': [0, 1]},
                                                    title={'text': "Job Match Score", 'font': {'size': 16}},
                                                    gauge={
                                                        'axis': {'range': [0, 100], 'tickwidth': 1},
                                                        'bar': {'color': "#4CAF50" if job_match_score >= 80 else "#FFA500" if job_match_score >= 60 else "#FF4444"},
                                                        'bgcolor': "white",
                                                        'borderwidth': 2,
                                                        'bordercolor': "gray",
                                                        'steps': [
                                                            {'range': [0, 40], 'color': 'rgba(255, 68, 68, 0.2)'},
                                                            {'range': [40, 60], 'color': 'rgba(255, 165, 0, 0.2)'},
                                                            {'range': [60, 80], 'color': 'rgba(255, 214, 0, 0.2)'},
                                                            {'range': [80, 100], 'color': 'rgba(76, 175, 80, 0.2)'}
                                                        ],
                                                        'threshold': {
                                                            'line': {'color': "red", 'width': 4},
                                                            'thickness': 0.75,
                                                            'value': 60
                                                        }
                                                    }
                                                ))
                                                
                                                fig3.update_layout(
                                                    height=250,
                                                    margin=dict(l=20, r=20, t=50, b=20),
                                                )
                                                
                                                st.plotly_chart(fig3, use_container_width=True)
                                                
                                                match_status = "Excellent Match" if job_match_score >= 80 else "Good Match" if job_match_score >= 60 else "Low Match"
                                                st.markdown(f"<div style='text-align: center; font-weight: bold;'>{match_status}</div>", unsafe_allow_html=True)
                                            
                                            with col2:
                                                st.markdown("""
                                                <div style="background-color: #262730; padding: 20px; border-radius: 10px; height: 100%;">
                                                    <h4 style="color: #ffffff; margin-bottom: 15px;">What This Means</h4>
                                                    <p style="color: #ffffff;">This score represents how well your resume matches the specific job description you provided.</p>
                                                    <ul style="color: #ffffff; padding-left: 20px;">
                                                        <li><strong>80-100:</strong> Excellent match - your resume is highly aligned with this job</li>
                                                        <li><strong>60-79:</strong> Good match - your resume matches many requirements</li>
                                                        <li><strong>Below 60:</strong> Consider tailoring your resume more specifically to this job</li>
                                                    </ul>
                                                </div>
                                                """, unsafe_allow_html=True)
                                    

                                    # Format the full response with better styling
                                    formatted_analysis = full_response
                                    
                                    # Replace section headers with styled headers
                                    section_styles = {
                                        "## Overall Assessment": """<div class="glass-card" style="margin-top: 2rem;">
                                            <h3 style="color: var(--primary); margin-bottom: 1.5rem;">
                                                <i class="fas fa-chart-line" style="margin-right: 15px;"></i> Overall Assessment
                                            </h3>
                                            <div style="color: var(--text-muted); line-height: 1.8;">""",
                                            
                                        "## Professional Profile Analysis": """<div class="glass-card" style="margin-top: 2rem;">
                                            <h3 style="color: var(--secondary); margin-bottom: 1.5rem;">
                                                <i class="fas fa-user-tie" style="margin-right: 15px;"></i> Professional Profile
                                            </h3>
                                            <div style="color: var(--text-muted); line-height: 1.8;">""",
                                            
                                        "## Skills Analysis": """<div class="glass-card" style="margin-top: 2rem;">
                                            <h3 style="color: var(--primary-alt); margin-bottom: 1.5rem;">
                                                <i class="fas fa-tools" style="margin-right: 15px;"></i> Skills Analysis
                                            </h3>
                                            <div style="color: var(--text-muted); line-height: 1.8;">""",
                                            
                                        "## Experience Analysis": """<div class="report-section">
                                            <h3 style="color: var(--accent); margin-bottom: 1.5rem;">
                                                <i class="fas fa-briefcase" style="margin-right: 15px;"></i> Experience Analysis
                                            </h3>
                                            <div style="color: var(--text-muted); line-height: 1.8;">""",
                                            
                                        "## Education Analysis": """<div class="report-section">
                                            <h3 style="background: linear-gradient(90deg, #854d0e, #eab308); color: white; padding: 10px; border-radius: 5px;">
                                                <i class="fas fa-graduation-cap"></i> Education Analysis
                                            </h3>
                                            <div class="section-content">""",
                                            
                                        "## Key Strengths": """<div class="report-section">
                                            <h3 style="background: linear-gradient(90deg, #166534, #22c55e); color: white; padding: 10px; border-radius: 5px;">
                                                <i class="fas fa-check-circle"></i> Key Strengths
                                            </h3>
                                            <div class="section-content">""",
                                            
                                        "## Areas for Improvement": """<div class="report-section">
                                            <h3 style="background: linear-gradient(90deg, #9f1239, #fb7185); color: white; padding: 10px; border-radius: 5px;">
                                                <i class="fas fa-exclamation-circle"></i> Areas for Improvement
                                            </h3>
                                            <div class="section-content">""",
                                            
                                        "## ATS Optimization Assessment": """<div class="report-section">
                                            <h3 style="background: linear-gradient(90deg, #0e7490, #06b6d4); color: white; padding: 10px; border-radius: 5px;">
                                                <i class="fas fa-robot"></i> ATS Optimization Assessment
                                            </h3>
                                            <div class="section-content">""",
                                            
                                        "## Recommended Courses": """<div class="report-section">
                                            <h3 style="background: linear-gradient(90deg, #5b21b6, #8b5cf6); color: white; padding: 10px; border-radius: 5px;">
                                                <i class="fas fa-book"></i> Recommended Courses
                                            </h3>
                                            <div class="section-content">""",
                                            
                                        "## Resume Score": """<div class="report-section">
                                            <h3 style="background: linear-gradient(90deg, #0369a1, #0ea5e9); color: white; padding: 10px; border-radius: 5px;">
                                                <i class="fas fa-star"></i> Resume Score
                                            </h3>
                                            <div class="section-content">""",
                                            
                                        "## Role Alignment Analysis": """<div class="report-section">
                                            <h3 style="background: linear-gradient(90deg, #7c2d12, #ea580c); color: white; padding: 10px; border-radius: 5px;">
                                                <i class="fas fa-bullseye"></i> Role Alignment Analysis
                                            </h3>
                                            <div class="section-content">""",
                                            
                                        "## Job Match Analysis": """<div class="report-section">
                                            <h3 style="background: linear-gradient(90deg, #4d7c0f, #84cc16); color: white; padding: 10px; border-radius: 5px;">
                                                <i class="fas fa-handshake"></i> Job Match Analysis
                                            </h3>
                                            <div class="section-content">""",
                                            
                                        "## Most Rare and Important Interview Questions": """<div class="report-section">
                                            <h3 style="background: linear-gradient(90deg, #f59e0b, #fbbf24); color: white; padding: 10px; border-radius: 5px;">
                                                <i class="fas fa-question-circle"></i> Most Rare and Important Interview Questions
                                            </h3>
                                            <div class="section-content">""",
                                    }
                                    
                                    # Apply the styling to each section
                                    for section, style in section_styles.items():
                                        if section in formatted_analysis:
                                            formatted_analysis = formatted_analysis.replace(
                                                section, style)
                                            # Add closing div tags
                                            next_section = False
                                            for next_sec in section_styles.keys():
                                                if next_sec != section and next_sec in formatted_analysis.split(style)[1]:
                                                    split_text = formatted_analysis.split(style)[1].split(next_sec)
                                                    formatted_analysis = formatted_analysis.split(style)[0] + style + split_text[0] + "</div></div>" + next_sec + "".join(split_text[1:])
                                                    next_section = True
                                                    break
                                            if not next_section:
                                                formatted_analysis = formatted_analysis + "</div></div>"
                                    
                                    # Remove any extra closing div tags that might have been added
                                    formatted_analysis = formatted_analysis.replace("</div></div></div></div>", "</div></div>")
                                    
                                    # Ensure we don't have any orphaned closing tags at the end
                                    if formatted_analysis.endswith("</div>"):
                                        # Count opening and closing div tags
                                        open_tags = formatted_analysis.count("<div")
                                        close_tags = formatted_analysis.count("</div>")
                                        
                                        # If we have more closing than opening tags, remove the extras
                                        if close_tags > open_tags:
                                            excess = close_tags - open_tags
                                            formatted_analysis = formatted_analysis[:-6 * excess]
                                    
                                    # Clean up any visible HTML tags that might appear in the text
                                    formatted_analysis = formatted_analysis.replace("&lt;/div&gt;", "")
                                    formatted_analysis = formatted_analysis.replace("&lt;div&gt;", "")
                                    formatted_analysis = formatted_analysis.replace("<div>", "<div>")  # Ensure proper opening
                                    formatted_analysis = formatted_analysis.replace("</div>", "</div>")  # Ensure proper closing
                                    
                                    # Add CSS for the report
                                    st.markdown("""
                                    <style>
                                        .report-section {
                                            margin-bottom: 25px;
                                            border: 1px solid #4B4B4B;
                                            border-radius: 8px;
                                            overflow: hidden;
                                        }
                                        .section-content {
                                            padding: 15px;
                                            background-color: #262730;
                                            color: #ffffff;
                                        }
                                        .report-section h3 {
                                            margin-top: 0;
                                            font-weight: 600;
                                        }
                                        .report-section ul {
                                            padding-left: 20px;
                                        }
                                        .report-section p {
                                            color: #ffffff;
                                            margin-bottom: 10px;
                                        }
                                        .report-section li {
                                            color: #ffffff;
                                            margin-bottom: 5px;
                                        }
                                    </style>
                                    """, unsafe_allow_html=True)

                                    # Display the formatted analysis
                                    st.markdown(f"""
                                    <div style="background-color: #262730; padding: 20px; border-radius: 10px; border: 1px solid #4B4B4B; color: #ffffff;">
                                        {formatted_analysis}
                                    </div>
                                    """, unsafe_allow_html=True)

                                    # Create a PDF report
                                    pdf_buffer = self.ai_analyzer.generate_pdf_report(
                                        analysis_result={
                                            "score": resume_score,
                                            "ats_score": ats_score,
                                            "model_used": model_used,
                                            "full_response": full_response,
                                            "strengths": analysis_result.get("strengths", []),
                                            "weaknesses": analysis_result.get("weaknesses", []),
                                            "used_custom_job_desc": st.session_state.get('used_custom_job_desc', False),
                                            "custom_job_description": custom_job_description if st.session_state.get('used_custom_job_desc', False) else ""
                                        },
                                        candidate_name=st.session_state.get(
                                            'candidate_name', 'Candidate'),
                                        job_role=selected_role
                                    )

                                    # PDF download button
                                    if pdf_buffer:
                                        st.download_button(
                                            label="📊 Download PDF Report",
                                            data=pdf_buffer,
                                            file_name=f"resume_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                                            mime="application/pdf",
                                            width='stretch',
                                            on_click=lambda: st.balloons()
                                        )
                                    else:
                                        st.error("PDF generation failed. Please try again later.")
                                else:
                                    st.error(f"Analysis failed: {analysis_result.get('error', 'Unknown error')}")
                        except Exception as ai_error:
                            st.error(f"Error during AI analysis: {str(ai_error)}")
                            import traceback as tb
                            st.code(tb.format_exc())

        with analyzer_tabs[2]:
            st.markdown("""
            <div style='background-color: #1e1e1e; padding: 20px; border-radius: 10px; margin: 10px 0;'>
                <h3>💡 AI Interview Preparation</h3>
                <p>Enter a company and role to scrape <b>real-world</b> interview questions asked by recruiters and candidates.</p>
            </div>
            """, unsafe_allow_html=True)
            
            prep_col1, prep_col2 = st.columns(2)
            with prep_col1:
                prep_company = st.text_input("Company Name", placeholder="e.g. Google, Zomato, Razorpay")
            with prep_col2:
                prep_role = st.text_input("Job Role", placeholder="e.g. Software Engineer, Product Manager")
            
            if st.button("🚀 Fetch Real Questions", type="primary", use_container_width=True):
                if prep_company and prep_role:
                    from utils.interview_fetcher import InterviewFetcher
                    fetcher = InterviewFetcher()
                    
                    questions, provider, context = fetcher.fetch_all(prep_company, prep_role)
                    
                    if questions:
                        st.session_state.prep_results = {
                            "questions": questions,
                            "context": context,
                            "company": prep_company,
                            "role": prep_role
                        }
                    else:
                        st.error("Currently unable to provide questions for this role. Please try again later.")
                else:
                    st.warning("Please provide both company name and role.")
            
            if 'prep_results' in st.session_state:
                res = st.session_state.prep_results
                st.markdown(f"## 🎯 Real Questions: {res['role']} at {res['company']}")
                st.info(f"**Tier:** {res['context'].get('tier')} | **Domain:** {res['context'].get('domain')}")
                
                for q in res['questions']:
                    badge_color = "#f59e0b" if q['importance'] == 'Rare' else "#4CAF50"
                    st.markdown(f"""
                        <div style="background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 8px; margin-bottom: 15px; border-left: 5px solid {badge_color};">
                            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">
                                <span style="background: {badge_color}; color: white; padding: 3px 10px; border-radius: 50px; font-size: 0.75rem; font-weight: bold;">{q['importance'].upper()}</span>
                                <span style="color: #00bfa5; font-size: 0.85rem; font-weight: bold;">🏢 {q['company']}</span>
                            </div>
                            <div style="font-size: 1.1rem; font-weight: 600; margin-bottom: 10px; color: #fff;">{q['question']}</div>
                            <div style="background: rgba(0, 191, 165, 0.05); padding: 10px; border-radius: 5px; border-left: 2px solid #00bfa5;">
                                <div style="color: #00bfa5; font-size: 0.75rem; font-weight: bold; text-transform: uppercase; margin-bottom: 4px;">Context / Why it's asked</div>
                                <div style="color: #ccc; font-size: 0.9rem; line-height: 1.4;">{q['reason']}</div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

        with analyzer_tabs[3]:
            st.markdown("""
            <div style='background-color: #1a1a1a; padding: 25px; border-radius: 15px; border: 1px solid #333; margin-bottom: 25px;'>
                <h2 style='color: #4CAF50; margin-bottom: 10px;'>🎙️ AI Voice-to-Voice Mock Interview</h2>
                <p style='color: #888;'>Practice your interview skills with our formal AI interviewer. Scraped real-world questions will be used to test you.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Initialize Utilities
            audio_utils = AudioUtils()
            interview_manager = InterviewManager()
            
            # 1. Interview is Active
            if 'interview' in st.session_state and not st.session_state.interview.get('is_complete', False):
                session = st.session_state.interview
                
                # Header Section
                st.markdown(f"### {session['role']} Interview at {session['company']}")
                progress = 0
                if session['current_step'].startswith('question_'):
                    progress = (session['question_index'] + 1) / (session['target_length'] + 2) # +2 for Greeting & Intro
                
                st.progress(progress)
                
                # Main Interaction Loop
                chat_container = st.container(height=400)
                
                with chat_container:
                    for item in session['transcript']:
                        with st.chat_message(item['role'].lower()):
                            st.write(item['text'])
                            if item['role'] == "User" and 'score' in item:
                                # Show inline feedback
                                st.markdown(f"⭐ **Score:** {item['score']}/10")
                                st.caption(f"Analysis: {item['feedback']}")
                
                # Logic for current step
                if 'last_handled_step' not in st.session_state or st.session_state.last_handled_step != session['current_step']:
                    # AI needs to speak
                    message = ""
                    if session['current_step'] == "greeting":
                        message = f"Hello! I am your interviewer today for the '{session['role']}' position at '{session['company']}'. I'll be asking you {session['target_length']} questions. To start, could you please tell me a bit about yourself?"
                    elif session['current_step'] == "intro":
                        message = "Thank you. Let's get started with the first question."
                        session['current_step'] = "question_0"
                        st.rerun()
                    elif session['current_step'].startswith('question_'):
                        idx = session['question_index']
                        if idx < len(session['questions']):
                            message = session['questions'][idx]['question']
                        else:
                            # If we ran out of scraped questions, AI generates one
                            prompt = f"Ask a formal interview question for {session['role']} at {session['company']}."
                            from utils.llm_orchestrator import LLMOrchestrator
                            message, _ = LLMOrchestrator().generate_content(prompt)
                    elif session['current_step'] == "conclusion":
                        message = "That concludes our interview. Thank you for your time. Your report is now ready for download."
                        session['is_complete'] = True
                    
                    if message:
                        session['transcript'].append({"role": "AI", "text": message, 
                                                     "question_idx": session['question_index'] if session['current_step'].startswith('question_') else None})
                        st.session_state.last_handled_step = session['current_step']
                        audio = audio_utils.text_to_speech(message, mode=session['language_mode'])
                        audio_utils.autoplay_audio(audio)
                        
                        # Handle Continuous Mode JS Bridge
                        if session.get('continuous_mode'):
                            # Inject JS to auto-click the mic recorder after audio finishes
                            st.components.v1.html("""
                                <script>
                                    window.parent.addEventListener('message', function(event) {
                                        if (event.data.type === 'audio_finished') {
                                            console.log("Audio finished event received in app.py bridge");
                                            // Find the mic recorder button and click it
                                            const buttons = window.parent.document.querySelectorAll('button');
                                            for(const btn of buttons) {
                                                if(btn.innerText.includes("Click to Start Recording")) {
                                                    btn.click();
                                                    console.log("Auto-started recorder");
                                                    break;
                                                }
                                            }
                                        }
                                    });
                                </script>
                            """, height=0, width=0)
                            
                        st.rerun()
                
                # User Input Section
                if not session['is_complete']:
                    st.markdown("---")
                    st.write("🎙️ **Record your answer below:**")
                    audio_input = mic_recorder(
                        start_prompt="Click to Start Recording",
                        stop_prompt="Click to Stop & Send",
                        key='recorder',
                        use_container_width=True
                    )
                    
                    if audio_input:
                        with st.spinner("Processing..."):
                            transcript = audio_utils.transcribe_audio(audio_input['bytes'])
                            session['transcript'].append({"role": "User", "text": transcript})
                            
                            # Process based on step
                            if session['current_step'] == "greeting":
                                session['current_step'] = "intro"
                            elif session['current_step'].startswith('question_'):
                                # Evaluate Answer
                                q_text = session['transcript'][-2]['text']
                                evaluation = interview_manager.evaluate_answer(q_text, transcript)
                                # Append evaluation to transcript for report
                                session['transcript'][-1].update(evaluation)
                                
                                session['question_index'] += 1
                                if session['question_index'] >= session['target_length']:
                                    session['current_step'] = "conclusion"
                                else:
                                    session['current_step'] = f"question_{session['question_index']}"
                            
                            st.rerun()
            
            # 3. Post Interview - Results Dashboard
            elif 'interview' in st.session_state and st.session_state.interview.get('is_complete', False):
                session = st.session_state.interview
                st.success("🎉 Interview Completed!")
                
                # Store report in session state to avoid regeneration issues
                if 'final_report_pdf' not in st.session_state:
                    with st.spinner("Analyzing your performance and generating report..."):
                        st.session_state.final_report_pdf = interview_manager.generate_pdf_report()
                
                # Show summary stats
                total_q = session['target_length']
                total_score = sum(item.get('score', 0) for item in session['transcript'] if item['role'] == "User")
                avg_score = total_score / total_q if total_q > 0 else 0
                
                col_r1, col_r2, col_r3 = st.columns(3)
                col_r1.metric("Average Score", f"{avg_score:.1f}/10")
                col_r2.metric("Questions Faced", total_q)
                col_r3.metric("Status", "Completed")
                
                st.download_button(
                    label="📄 Download Detailed Performance Report (PDF)",
                    data=st.session_state.final_report_pdf,
                    file_name=f"interview_report_{session['company']}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary"
                )
                
                # Show full transcript with detailed feedback
                with st.expander("👁️ View Full Transcript & Detailed Feedback", expanded=True):
                    for item in session['transcript']:
                        with st.chat_message(item['role'].lower()):
                            st.write(item['text'])
                            if item['role'] == "User" and 'score' in item:
                                st.markdown(f"**Score:** {item['score']}/10")
                                st.markdown(f"**Analysis:** {item['feedback']}")
                                st.info(f"💡 **Tip:** {item.get('improvement', 'N/A')}")
                
                if st.button("🔄 Start New Interview", use_container_width=True):
                    if 'final_report_pdf' in st.session_state:
                        del st.session_state.final_report_pdf
                    del st.session_state.interview
                    if 'last_handled_step' in st.session_state:
                        del st.session_state.last_handled_step
                    st.rerun()

            # 2. Setup Panel - Only show if no interview
            else:
                # Setup Panel
                col_s1, col_s2, col_s3 = st.columns(3)
                with col_s1:
                    mock_role = st.text_input("Target Role", placeholder="e.g. Software Engineer", key="mock_role_input")
                with col_s2:
                    mock_company = st.text_input("Target Company", placeholder="e.g. Google", key="mock_company_input")
                col_s3, col_s4 = st.columns([2, 1])
                with col_s3:
                    mock_length = st.slider("Number of Questions", 3, 8, 5)
                with col_s4:
                    continuous_mode = st.toggle("🔄 Continuous Listening", value=True, help="Automatically starts microphone after AI speaks")
                
                mock_lang = st.radio("Language Mode", ["English", "Hinglish"], horizontal=True)
                
                if st.button("🚀 Start Voice Interview", type="primary", use_container_width=True):
                    if mock_role and mock_company:
                        # Try to get scraped questions or use fallback
                        from utils.interview_fetcher import InterviewFetcher
                        fetcher = InterviewFetcher()
                        with st.spinner("Preparing your interview board..."):
                            questions, _, context = fetcher.fetch_all(mock_company, mock_role)
                            interview_manager.initialize_session(questions or [], mock_role, mock_company, mock_length, mock_lang)
                            st.session_state.interview['continuous_mode'] = continuous_mode
                            st.rerun()
                    else:
                        st.warning("Please provide both role and company.")

        st.toast("Check out these repositories: [Awesome Java](https://github.com/Hunterdii/Awesome-Java)", icon="ℹ️")


    def render_home(self):
        apply_modern_styles()
        
        # Premium Hero Section
        hero_section(
            "Smart Resume AI",
            "THE FUTURE OF CAREER ACCELERATION",
            "Leverage the power of Generative AI to decode your career potential. Analyze your resume with industry-leading accuracy and build professional profiles that get you hired at top-tier companies."
        )
        
        # Features Grid
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            feature_card(
                "fas fa-robot",
                "Neural Analysis",
                "Our advanced LLM-powered engine dissects every bullet point in your resume to ensure it matches specific job role requirements."
            )
        with col_f2:
            feature_card(
                "fas fa-magic",
                "Precision Builder",
                "Generate ATS-optimized resumes in seconds. Choose from professional templates designed to pass through any recruiter's system."
            )
        with col_f3:
            feature_card(
                "fas fa-handshake",
                "Recruiter Direct",
                "Enable recruiter visibility and get discovered by hiring managers looking for your specific skill set and expertise."
            )
        
        st.toast("Check out these repositories: [AI-Nexus(AI/ML)](https://github.com/Hunterdii/AI-Nexus)", icon="ℹ️")

    def render_recruiter_page(self):
        """Render the new recruiter dashboard for candidate discovery"""
        from ui_components import candidate_card
        from config.database import get_candidates_for_recruiter_filter
        
        page_header(
            "Recruiter Hub",
            "Connect with top talent analyzed by our AI system"
        )
        
        # Filters Sidebar/Header
        with st.expander("🔍 Filter Candidates", expanded=True):
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                search_skills = st.multiselect("Skills Required", 
                    ["Python", "JavaScript", "React", "Vue.js", "Angular", "Node.js", "Java", "SQL", "NoSQL", "Docker", "Kubernetes", "DevOps", "AWS", "Azure", "GCP", "Machine Learning", "Data Science", "UI/UX", "Project Management"])
            with col2:
                search_location = st.text_input("Location (City/Remote)")
            with col3:
                min_score = st.slider("Min. ATS Score", 0, 100, 50)
        
        if st.button("Search Candidates", type="primary"):
            with st.spinner("Finding matches..."):
                candidates = get_candidates_for_recruiter_filter(
                    skills=search_skills if search_skills else None,
                    location=search_location if search_location else None,
                    min_ats_score=min_score
                )
                
                if not candidates:
                    st.info("No candidates matching your criteria were found.")
                else:
                    st.write(f"Found {len(candidates)} matching candidates")
                    
                    # Responsive grid for candidates
                    cols = st.columns(2)
                    for idx, cand in enumerate(candidates):
                        with cols[idx % 2]:
                            candidate_card(
                                name=cand['name'],
                                role=cand['role'],
                                skills=cand['skills'],
                                location=cand['location'],
                                score=int(cand['ats_score'] or 0),
                                experience=cand['experience']
                            )
        else:
            # Initial state - show all recent candidates
            candidates = get_candidates_for_recruiter_filter(min_ats_score=0)
            if candidates:
                st.markdown("### 🌐 Talent Discovery")
                st.write(f"Showing all {len(candidates)} active candidates")
                cols = st.columns(2)
                for idx, cand in enumerate(candidates):
                    with cols[idx % 2]:
                        candidate_card(
                            name=cand['name'],
                            role=cand['role'],
                            skills=cand['skills'],
                            location=cand['location'],
                            score=int(cand['ats_score'] or 0),
                            experience=cand['experience']
                        )
            else:
                st.info("No candidates analyzed yet. Resumes uploaded by users will appear here.")

        # Call-to-Action with Streamlit navigation
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("Get Started", key="get_started_btn", 
                        help="Click to start analyzing your resume",
                        type="primary",
                        width='stretch'):
                cleaned_name = "🔍 RESUME ANALYZER".lower().replace(" ", "_").replace("🔍", "").strip()
                st.session_state.page = cleaned_name
                st.rerun()

    def render_profile_page(self):
        """Render the user's application profile for verification"""
        page_header(
            "My Application Profile",
            "This data is used to auto-fill your job applications"
        )
        
        if 'candidate_profile' not in st.session_state:
            st.warning("No profile data found. Please analyze a resume first!")
            return
            
        profile = st.session_state.candidate_profile
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📝 Personal Details")
            with st.container():
                st.text_input("Full Name", value=profile.get('full_name', ''), key="prof_name")
                st.text_input("Email", value=profile.get('email', ''), key="prof_email")
                st.text_input("Phone", value=profile.get('phone', ''), key="prof_phone")
                st.text_input("Location", value=profile.get('location', ''), key="prof_loc")
        
        with col2:
            st.markdown("### 🔗 Links & Professional")
            with st.container():
                st.text_input("LinkedIn", value=profile.get('linkedin', ''), key="prof_link")
                st.text_input("Portfolio", value=profile.get('portfolio', ''), key="prof_port")
                
                st.markdown("#### 🔒 LinkedIn Login (Required for Auto-Fill)")
                st.text_input("LinkedIn Email", value=profile.get('li_email', ''), key="prof_li_email")
                st.text_input("LinkedIn Password", value=profile.get('li_password', ''), type="password", key="prof_li_pass")
                
                st.text_area("Experience Summary", value=profile.get('experience_summary', ''), height=150, key="prof_sum")
        
        st.markdown("### 🛠️ Skills Extracted")
        skills = profile.get('skills', [])
        if isinstance(skills, str):
            skills = [s.strip() for s in skills.split(',')]
        
        st.write(", ".join(skills) if skills else "No skills identified")
        
        if st.button("Save Profile Changes", type="primary"):
            st.session_state.candidate_profile.update({
                'full_name': st.session_state.prof_name,
                'email': st.session_state.prof_email,
                'phone': st.session_state.prof_phone,
                'location': st.session_state.prof_loc,
                'linkedin': st.session_state.prof_link,
                'portfolio': st.session_state.prof_port,
                'li_email': st.session_state.prof_li_email,
                'li_password': st.session_state.prof_li_pass,
                'experience_summary': st.session_state.prof_sum
            })
            st.success("Profile updated successfully!")

    def render_job_search(self):
        """Render the job search page"""
        render_job_search()

        st.toast("Check out these repositories: [GeeksforGeeks-POTD](https://github.com/Hunterdii/GeeksforGeeks-POTD)", icon="ℹ️")


    def render_feedback_page(self):
        """Render the feedback page"""
        apply_modern_styles()
        
        # Page Header
        page_header(
            "Feedback & Suggestions",
            "Help us improve by sharing your thoughts"
        )
        
        # Initialize feedback manager
        feedback_manager = FeedbackManager()
        
        # Create tabs for form and stats
        form_tab, stats_tab = st.tabs(["Submit Feedback", "Feedback Stats"])
        
        with form_tab:
            feedback_manager.render_feedback_form()
            
        with stats_tab:
            feedback_manager.render_feedback_stats()

        st.toast("Check out these repositories: [TryHackMe Free Rooms](https://github.com/Hunterdii/tryhackme-free-rooms)", icon="ℹ️")


    def show_repo_notification(self):
        message = """
# <div style="background-color: #1e1e1e; border-radius: 10px; border: 1px solid #4b6cb7; padding: 10px; margin: 10px 0; color: white;">
#     <div style="margin-bottom: 10px;">Check out these other repositories:</div>
#     <div style="margin-bottom: 5px;"><b>Hacking Resources:</b></div>
#     <ul style="margin-top: 0; padding-left: 20px;">
#         <li><a href="https://github.com/Hunterdii/tryhackme-free-rooms" target="_blank" style="color: #4CAF50;">TryHackMe Free Rooms</a></li>
#         <li><a href="https://github.com/Hunterdii/Awesome-Hacking" target="_blank" style="color: #4CAF50;">Awesome Hacking</a></li>
#     </ul>
#     <div style="margin-bottom: 5px;"><b>Programming Languages:</b></div>
#     <ul style="margin-top: 0; padding-left: 20px;">
#         <li><a href="https://github.com/Hunterdii/Awesome-Java" target="_blank" style="color: #4CAF50;">Awesome Java</a></li>
#         <li><a href="https://github.com/Hunterdii/30-Days-Of-Rust" target="_blank" style="color: #4CAF50;">30 Days Of Rust</a></li>
#     </ul>
#     <div style="margin-bottom: 5px;"><b>Data Structures & Algorithms:</b></div>
#     <ul style="margin-top: 0; padding-left: 20px;">
#         <li><a href="https://github.com/Hunterdii/GeeksforGeeks-POTD" target="_blank" style="color: #4CAF50;">GeeksforGeeks POTD</a></li>
#         <li><a href="https://github.com/Hunterdii/Leetcode-POTD" target="_blank" style="color: #4CAF50;">Leetcode POTD</a></li>
#     </ul>
#     <div style="margin-bottom: 5px;"><b>AI/ML Projects:</b></div>
#     <ul style="margin-top: 0; padding-left: 20px;">
#         <li><a href="https://github.com/Hunterdii/AI-Nexus" target="_blank" style="color: #4CAF50;">AI Nexus</a></li>
#     </ul>
#     <div style="margin-top: 10px;">If you find this project helpful, please consider ⭐ starring the repo!</div>
# </div>
# """
#         st.sidebar.markdown(message, unsafe_allow_html=True)


    def main(self):
        """Main application entry point"""
        self.apply_global_styles()
        
        # Admin login/logout in sidebar
        with st.sidebar:
            st_lottie(self.load_lottie_url("https://assets5.lottiefiles.com/packages/lf20_xyadoh9h.json"), height=200, key="sidebar_animation")
            st.title("Smart Resume AI")
            st.markdown("---")
            
            # Navigation buttons
            for page_name in self.pages.keys():
                if st.button(page_name, width='stretch'):
                    cleaned_name = page_name.lower().replace(" ", "_").replace("🏠", "").replace("🔍", "").replace("📝", "").replace("📊", "").replace("🎯", "").replace("💬", "").replace("ℹ️", "").strip()
                    st.session_state.page = cleaned_name
                    st.rerun()

            # Add some space before admin login
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown("---")

            # Admin Login/Logout section at bottom
            if st.session_state.get('is_admin', False):
                st.success(f"Logged in as: {st.session_state.get('current_admin_email')}")
                if st.button("Logout", key="logout_button"):
                    try:
                        log_admin_action(st.session_state.get('current_admin_email'), "logout")
                        st.session_state.is_admin = False
                        st.session_state.current_admin_email = None
                        st.success("Logged out successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error during logout: {str(e)}")
            else:
                with st.expander("👤 Admin Login"):
                    admin_email_input = st.text_input("Email", key="admin_email_input")
                    admin_password = st.text_input("Password", type="password", key="admin_password_input")
                    if st.button("Login", key="login_button"):
                            try:
                                if verify_admin(admin_email_input, admin_password):
                                    st.session_state.is_admin = True
                                    st.session_state.current_admin_email = admin_email_input
                                    log_admin_action(admin_email_input, "login")
                                    st.success("Logged in successfully!")
                                    st.rerun()
                                else:
                                    st.error("Invalid credentials")
                            except Exception as e:
                                st.error(f"Error during login: {str(e)}")
        
            # Display the repository notification in the sidebar
            self.show_repo_notification()

        # Force home page on first load
        if 'initial_load' not in st.session_state:
            st.session_state.initial_load = True
            st.session_state.page = 'home'
            st.rerun()
        
        # Get current page and render it
        current_page = st.session_state.get('page', 'home')
        
        # Create a mapping of cleaned page names to original names
        page_mapping = {name.lower().replace(" ", "_").replace("🏠", "").replace("🔍", "").replace("📝", "").replace("📊", "").replace("🎯", "").replace("💬", "").replace("ℹ️", "").strip(): name 
                       for name in self.pages.keys()}
        
        # Render the appropriate page
        if current_page in page_mapping:
            self.pages[page_mapping[current_page]]()
        else:
            # Default to home page if invalid page
            self.render_home()
    
        # Add footer to every page
        self.add_footer()

if __name__ == "__main__":
    app = ResumeApp()
    app.main()
#!/usr/bin/env python3
"""Remove duplicate navigation entries from app.py"""

import re

# Read the file
with open('app.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Find the pages dictionary and clean it
# Replace the problematic section with clean version
old_pattern = r'self\.pages = \{[^}]*"💬 AI CHATBOT"[^}]*"ℹ️ ABOUT"[^}]*\}'

new_dict = '''self.pages = {
            "🏠 HOME": self.render_home,
            "🔍 RESUME ANALYZER": self.render_analyzer,
            "📝 RESUME BUILDER": self.render_builder,
            "💬 AI CHATBOT": self.render_ai_chatbot,
            "📊 DASHBOARD": self.render_dashboard,
            "🤝 RECRUITERS": self.render_recruiter_page,
            "🎯 JOB SEARCH": self.render_job_search,
            "👤 MY PROFILE": self.render_profile_page,
            "💬 FEEDBACK": self.render_feedback_page,
            "ℹ️ ABOUT": self.render_about
        }'''

content = re.sub(old_pattern, new_dict, content, flags=re.DOTALL)

# Write back
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Duplicates removed successfully!")

import re

# Read the file
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the problematic section by finding the pages dict and reconstructing it cleanly
old_pattern = r'self\.pages = \{[^}]+?\}'
new_pages = '''self.pages = {
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

# Use multiline regex to find and replace
content = re.sub(old_pattern, new_pages, content, flags=re.DOTALL)

# Write back
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed pages dictionary successfully')

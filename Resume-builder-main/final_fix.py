#!/usr/bin/env python3
"""Fix the pages dictionary in app.py by removing corrupted entries."""

import os
import sys

# Navigate to correct directory
script_dir = r'c:\Users\shub\Downloads\Resume-builder-main\Resume-builder-main'
os.chdir(script_dir)

# Read the file
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Count problematic lines before
import re
matches_before = len(re.findall(r'"[^"]* AI CHATBOT".*?self\.render_ai_chatbot,', content))
print(f"Found {matches_before} AI CHATBOT entries before fix")

# Find the start of pages dict
pages_start = content.find('self.pages = {')
if pages_start == -1:
    print("Could not find pages dict!")
    sys.exit(1)

# Find the end of pages dict
pages_end = content.find('}', pages_start)
if pages_end == -1:
    print("Could not find end of pages dict!")
    sys.exit(1)

pages_end += 1

# Extract the dict
old_dict = content[pages_start:pages_end]

# Build new dict (clean version)
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

# Replace
new_content = content[:pages_start] + new_dict + content[pages_end:]

# Write back
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ Successfully fixed pages dictionary!")
print(f"Replaced {len(old_dict)} chars with {len(new_dict)} chars")

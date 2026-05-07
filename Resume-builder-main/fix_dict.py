#!/usr/bin/env python3
import os

# Read file
with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Process lines
new_lines = []
in_pages_dict = False
seen_ai_chatbot = False
seen_dashboard = False

for line in lines:
    # If we're entering the pages dictionary
    if 'self.pages = {' in line:
        in_pages_dict = True
        new_lines.append(line)
        continue
    
    # If we've exited the pages dictionary
    if in_pages_dict and line.strip() == '}':
        in_pages_dict = False
        seen_ai_chatbot = False
        seen_dashboard = False
        new_lines.append(line)
        continue
    
    # Skip malformed emoji lines (they contain the replacement character)
    if in_pages_dict and ('AI CHATBOT' in line or 'DASHBOARD' in line):
        # Skip if it has the replacement character
        if '\ufffd' in line or '�' in line:
            continue
        # For correct entries, only add once
        if '💬 AI CHATBOT' in line:
            if not seen_ai_chatbot:
                new_lines.append(line)
                seen_ai_chatbot = True
            continue
        if '📊 DASHBOARD' in line and 'self.render_dashboard' in line:
            if not seen_dashboard:
                new_lines.append(line)
                seen_dashboard = True
            continue
    
    new_lines.append(line)

# Write back
with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✓ Fixed pages dictionary - removed duplicates")

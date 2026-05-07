import re

# Read as binary to get exact bytes
with open('app.py', 'rb') as f:
    content = f.read()

# The malformed entries have wrong Unicode character
# Let's search for the pattern and remove lines with the replacement character
lines = content.decode('utf-8', errors='replace').split('\n')
output_lines = []

skip_dup_ai = 0
skip_dup_dash = 0

for i, line in enumerate(lines):
    # Skip lines with the corrupted Unicode character (replacement char)
    if '\ufffd' in line or 'AI CHATBOT' in line and line.strip().startswith('"'):
        # If this line has a corrupted character, skip it
        if '\ufffd' in line:
            continue
        
        # For AI CHATBOT lines, only keep one
        if '💬 AI CHATBOT' in line:
            if skip_dup_ai == 0:
                output_lines.append(line)
                skip_dup_ai = 1
            continue
        
        # If it's the malformed one (no emoji emoji at start), skip
        if not line.strip().startswith('"💬') and 'AI CHATBOT' in line:
            continue
    
    # Similarly for DASHBOARD
    if 'DASHBOARD' in line and line.strip().startswith('"'):
        if '\ufffd' in line:
            continue
        
        if '📊 DASHBOARD' in line:
            if skip_dup_dash == 0:
                output_lines.append(line)
                skip_dup_dash = 1
            continue
        
        # If it's malformed (no leading emoji), skip
        if not line.strip().startswith('"📊') and 'DASHBOARD' in line:
            continue
    
    output_lines.append(line)

# Write back
with open('app.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output_lines))

print("Successfully fixed pages dictionary")

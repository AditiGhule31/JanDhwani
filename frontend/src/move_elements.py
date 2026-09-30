import os

filepath = r'c:\Users\HP\OneDrive\jandhwani local\frontend\src\components\login\Login.jsx'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Aadhaar Block
aadhaar_start = content.find('<div className="form-group">\n              <label>Aadhaar Number (UIDAI)')
# Find the end of Aadhaar block, which is right before the GPS block
aadhaar_end = content.find('<div className="form-group" style={{gridColumn: \'1 / -1\', background: \'#e3f2fd\'')
aadhaar_block = content[aadhaar_start:aadhaar_end]

# Security Block
sec_start = content.find('{/* Section 3: Security */}')
sec_end = content.find('            </div>\n          </div>\n          <button type="submit" className="auth-submit-btn">')
sec_block = content[sec_start:sec_end]

# Remove them
content = content[:sec_start] + content[sec_end:]
content = content.replace(aadhaar_block, '')

# Find insertion point
# The end of form-column 1 is before <div className="form-column">
insert_marker = '            </div>\n            <div className="form-column">'
insert_idx = content.find(insert_marker)

content = content[:insert_idx] + aadhaar_block + '\n' + sec_block + '\n' + content[insert_idx:]

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print('Done!')

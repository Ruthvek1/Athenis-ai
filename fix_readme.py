import re

with open("README.md", "r") as f:
    content = f.read()

# Replace the logo placeholder
content = content.replace(
    '<img src="https://via.placeholder.com/150x150/09090b/3b82f6?text=Athenis" alt="Athenis Logo" width="120" height="120" />',
    '<img src="frontend/public/assets/logo.png" alt="Athenis Logo" width="120" height="120" style="border-radius: 20%;" />'
)

# Extract the screenshots block
pattern = r"(## ✨ Key Features\n\n)(### 📸 Application Interface\n<div align=\"center\">\n  <img src=\"frontend/public/assets/dashboard\.png\" width=\"48%\" alt=\"System Dashboard\" />\n  <img src=\"frontend/public/assets/chat\.png\" width=\"48%\" alt=\"Athenis Chat\" />\n  <br/>\n  <img src=\"frontend/public/assets/admin\.png\" width=\"48%\" alt=\"Knowledge Base\" />\n  <img src=\"frontend/public/assets/login\.png\" width=\"48%\" alt=\"Login Portal\" />\n</div>\n)"
match = re.search(pattern, content)

if match:
    screenshot_block = match.group(2)
    # Remove it from Key Features
    content = content.replace(screenshot_block, "")
    
    # Insert it before the Table of Contents
    toc_pattern = r"(<br />\n\n## 📖 Table of Contents)"
    content = re.sub(toc_pattern, f"<br />\n\n{screenshot_block}\n\\1", content)
else:
    print("Screenshot block not found using regex, trying fallback.")
    # Fallback string replace if regex fails
    old_section = """## ✨ Key Features

### 📸 Application Interface
<div align="center">
  <img src="frontend/public/assets/dashboard.png" width="48%" alt="System Dashboard" />
  <img src="frontend/public/assets/chat.png" width="48%" alt="Athenis Chat" />
  <br/>
  <img src="frontend/public/assets/admin.png" width="48%" alt="Knowledge Base" />
  <img src="frontend/public/assets/login.png" width="48%" alt="Login Portal" />
</div>"""

    new_section = "## ✨ Key Features"
    screenshot_block = """### 📸 Application Interface
<div align="center">
  <img src="frontend/public/assets/dashboard.png" width="48%" alt="System Dashboard" />
  <img src="frontend/public/assets/chat.png" width="48%" alt="Athenis Chat" />
  <br/>
  <img src="frontend/public/assets/admin.png" width="48%" alt="Knowledge Base" />
  <img src="frontend/public/assets/login.png" width="48%" alt="Login Portal" />
</div>"""

    content = content.replace(old_section, new_section)
    content = content.replace("<br />\n\n## 📖 Table of Contents", f"<br />\n\n{screenshot_block}\n\n## 📖 Table of Contents")


with open("README.md", "w") as f:
    f.write(content)

print("README updated successfully.")

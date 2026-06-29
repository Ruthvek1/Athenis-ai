import os
import re
import subprocess

SOURCE_DIR = 'docs_source'
OUTPUT_FILE = 'Athenis_Technical_Documentation.md'

def process_markdown():
    # Concatenate all markdown files
    md_files = sorted([f for f in os.listdir(SOURCE_DIR) if f.endswith('.md')])
    full_content = ""
    for f in md_files:
        with open(os.path.join(SOURCE_DIR, f), 'r', encoding='utf-8') as file:
            full_content += file.read() + "\n\n"
            
    # Find all mermaid blocks
    mermaid_pattern = re.compile(r'```mermaid\n(.*?)\n```', re.DOTALL)
    
    diagram_count = 0
    def replace_mermaid(match):
        nonlocal diagram_count
        diagram_count += 1
        diagram_code = match.group(1)
        mmd_path = f"diagram_{diagram_count}.mmd"
        png_path = f"diagram_{diagram_count}.png"
        
        # Write to mmd file
        with open(mmd_path, 'w', encoding='utf-8') as mmd_file:
            mmd_file.write(diagram_code)
            
        # Run mmdc to convert to png
        print(f"Rendering diagram {diagram_count}...")
        try:
            subprocess.run(['mmdc', '-i', mmd_path, '-o', png_path, '-b', 'transparent', '-s', '2'], check=True)
            print(f"Successfully rendered {png_path}")
            # Replace code block with image tag
            return f"![Architecture Diagram]({png_path})\n*Figure: System Visualization {diagram_count}*"
        except Exception as e:
            print(f"Failed to render diagram {diagram_count}: {e}")
            return match.group(0) # fallback to raw code if it fails
            
    # Replace all matches
    final_content = mermaid_pattern.sub(replace_mermaid, full_content)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as out:
        out.write(final_content)
        
    print(f"Processed markdown written to {OUTPUT_FILE}")

if __name__ == "__main__":
    process_markdown()

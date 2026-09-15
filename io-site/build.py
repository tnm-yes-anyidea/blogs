import os
import re

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README_PATH = os.path.join(ROOT_DIR, "README.md")
SITE_INDEX_PATH = os.path.join(ROOT_DIR, "io-site", "index.html")

EXCLUDE_DIRS = {".git", ".github", "io-site", "data", "figures", "calculations"}

def extract_title_from_file(file_path):
    """Extract heading title from Markdown or LaTeX files."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Match Markdown # Title
    md_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if md_match:
        return md_match.group(1).strip()

    # Match LaTeX \title{...}
    tex_match = re.search(r"\\title\{(?:\textbf\{)?([^}]+)(?:\})?\}", content)
    if tex_match:
        return tex_match.group(1).replace("\\textbf{", "").replace("}", "").strip()

    return None

def scan_blogs():
    """Find all subdirectories containing .md or .tex blog files."""
    blogs = []
    
    for entry in os.listdir(ROOT_DIR):
        full_path = os.path.join(ROOT_DIR, entry)
        if os.path.isdir(full_path) and entry not in EXCLUDE_DIRS:
            title = None
            blog_file = None
            
            # Check for standard blog files in order of preference
            for filename in ["paper.md", "README.md", "paper.tex"]:
                file_path = os.path.join(full_path, filename)
                if os.path.exists(file_path):
                    extracted = extract_title_from_file(file_path)
                    if extracted:
                        title = extracted
                        blog_file = filename
                        break
            
            if title and blog_file:
                blogs.append({
                    "dir": entry,
                    "title": title,
                    "file": blog_file
                })
    return blogs

def update_root_readme(blogs):
    """Inject/Update the blogs list inside README.md automatically."""
    if not os.path.exists(README_PATH):
        print("Root README.md not found.")
        return

    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    start_marker = "<!-- BLOG-LIST-START -->"
    end_marker = "<!-- BLOG-LIST-END -->"

    blog_md_list = ["\n## Index of Blogs & Research\n"]
    for b in blogs:
        blog_md_list.append(f"* [{b['title']}](./{b['dir']}/{b['file']})")
    blog_md_list.append("\n")

    new_blog_section = f"{start_marker}\n" + "\n".join(blog_md_list) + f"{end_marker}"

    if start_marker in content and end_marker in content:
        pattern = re.compile(f"{re.escape(start_marker)}.*?{re.escape(end_marker)}", re.DOTALL)
        updated_content = pattern.sub(new_blog_section, content)
    else:
        updated_content = content + "\n\n" + new_blog_section

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(updated_content)
    print("Successfully updated root README.md with blog list.")

def generate_site_html(blogs):
    """Generate index.html for the io-site directory."""
    html_cards = []
    for b in blogs:
        card = f"""
        <li class="blog-card">
            <h3><a href="../{b['dir']}/{b['file']}">{b['title']}</a></h3>
            <p>Path: <code>{b['dir']}/{b['file']}</code></p>
        </li>
        """
        html_cards.append(card)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Blog Index</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <main class="container">
        <h1>Articles & Research Papers</h1>
        <ul class="blog-list">
            {"".join(html_cards)}
        </ul>
    </main>
</body>
</html>
"""
    with open(SITE_INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Generated site index at {SITE_INDEX_PATH}")

if __name__ == "__main__":
    found_blogs = scan_blogs()
    print(f"Found {len(found_blogs)} blog post(s):")
    for blog in found_blogs:
        print(f" - {blog['title']} ({blog['dir']})")
    
    update_root_readme(found_blogs)
    generate_site_html(found_blogs)

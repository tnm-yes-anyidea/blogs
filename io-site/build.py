import os
import re
import subprocess
import json

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXCLUDE_DIRS = {".git", ".github", "io-site", "data", "figures", "calculations", "quotes"}

# Sashimi UI handles native light/dark theming via the browser's prefers-color-scheme.
PANDOC_HEADER = """<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/sashimi-ui/default.theme.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/sashimi-ui/bundle.css">
<script>
MathJax = {
  tex: {
    inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
    displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
    processEscapes: true,
    packages: {'[+]': ['base', 'ams', 'noerrors', 'noundefined']}
  }
};
</script>
<script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
<style>
/* 
  Layout styling to center content and create the minimalist boxes 
  while letting Sashimi UI handle all typography and coloring.
*/
body { max-width: 800px; margin: 40px auto; padding: 0 20px; }
.blog-grid { display: flex; flex-direction: column; gap: 1rem; margin-top: 1.5rem; }
.blog-card {
    display: block;
    padding: 1.25rem 1.5rem;
    border: 1px solid var(--sm-color-border, #555);
    border-radius: 8px;
    text-decoration: none;
    color: inherit;
    transition: transform 0.15s ease, border-color 0.15s ease;
}
.blog-card h3 { margin: 0; font-size: 1.2rem; }
.blog-card:hover {
    border-color: var(--sm-color-primary, #d97706);
    transform: translateY(-2px);
}
.nav-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--sm-color-border, #555);
    padding-bottom: 1rem;
    margin-bottom: 2rem;
}
.nav-header h1 { margin: 0; font-size: 1.5rem; }
.github-icon { width: 24px; height: 24px; fill: currentColor; transition: opacity 0.2s; }
.github-icon:hover { opacity: 0.7; }
</style>
"""

def extract_title(file_path):
    folder_name = os.path.basename(os.path.dirname(file_path)).replace("-", " ").title()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        if file_path.endswith(".md"):
            match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            return match.group(1).strip() if match else folder_name
        else:
            match = re.search(r"\\title\{([\s\S]*?)\}", content)
            if match:
                raw_title = match.group(1)
                clean_title = re.sub(r"\\[a-zA-Z]+\{?", "", raw_title).replace("}", "").strip()
                return clean_title if clean_title else folder_name
            return folder_name
    except Exception:
        return folder_name

def compile_file(input_file, output_html, title):
    header_file = os.path.join(ROOT_DIR, "io-site", "_header.html")
    with open(header_file, "w", encoding="utf-8") as f:
        f.write(PANDOC_HEADER)

    input_format = "latex" if input_file.endswith(".tex") else "markdown"

    cmd = [
        "pandoc",
        f"--from={input_format}",
        input_file,
        "-o", output_html,
        "--standalone",
        "--mathjax",
        f"--metadata=title:{title}",
        "-H", header_file
    ]
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    if os.path.exists(header_file):
        os.remove(header_file)
        
    if res.returncode != 0:
        print(f"Error compiling {input_file}:\n{res.stderr}")
        return False
    return True

def load_quotes():
    quotes_path = os.path.join(ROOT_DIR, "quotes", "quotes.md")
    if not os.path.exists(quotes_path):
        return ""

    with open(quotes_path, "r", encoding="utf-8") as f:
        content = f.read()

    entries = [e.strip() for e in content.split("---") if e.strip()]
    cards = []

    for entry in entries:
        date_m = re.search(r"^#\s+(.+)$", entry, re.MULTILINE)
        topic_m = re.search(r"^##\s+(.+)$", entry, re.MULTILINE)
        quote_m = re.search(r"^>\s*\"?(.+?)\"?$", entry, re.MULTILINE)
        author_m = re.search(r"^—\s*(.+)$", entry, re.MULTILINE)

        date = date_m.group(1) if date_m else ""
        topic = topic_m.group(1) if topic_m else ""
        quote = quote_m.group(1) if quote_m else entry
        author = author_m.group(1) if author_m else "anonymous"

        # Leveraging native HTML tags so Sashimi UI can style them automatically
        cards.append(f"""
        <article style="margin-bottom: 2rem;">
            <div style="display: flex; justify-content: space-between; font-size: 0.9em; opacity: 0.7;">
                <span>{date}</span>
                <span>{topic}</span>
            </div>
            <blockquote>
                <p>“{quote}”</p>
                <footer>— <cite>{author}</cite></footer>
            </blockquote>
        </article>
        """)

    return "".join(cards)

def main():
    blogs = []
    print(f"Scanning directory: {ROOT_DIR}")
    
    for entry in sorted(os.listdir(ROOT_DIR)):
        full_path = os.path.join(ROOT_DIR, entry)
        if os.path.isdir(full_path) and entry not in EXCLUDE_DIRS:
            target_file = None
            for fname in ["paper.tex", "paper.md", "README.md"]:
                fpath = os.path.join(full_path, fname)
                if os.path.exists(fpath):
                    target_file = fpath
                    break
            
            if target_file:
                title = extract_title(target_file)
                out_html = os.path.join(full_path, "index.html")
                print(f"Building: {target_file} -> {out_html}")
                
                if compile_file(target_file, out_html, title):
                    blogs.append({"title": title, "path": f"{entry}/index.html"})

    # Wrapping the links into the blog-card class for the minimalist box look
    list_items = "".join([f'<a href="{b["path"]}" class="blog-card"><h3>{b["title"]}</h3></a>' for b in blogs])
    quotes_html = load_quotes()

    main_index = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Blog Index</title>
    {PANDOC_HEADER}
</head>
<body>
    <header class="nav-header">
        <h1>blogs</h1>
        <a href="https://github.com/tnm-yes-anyidea/blogs" target="_blank" rel="noopener noreferrer" aria-label="GitHub Repository">
            <svg class="github-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
            </svg>
        </a>
    </header>

    <main>
        <h2>Articles & Research Papers</h2>
        <div class="blog-grid">
            {list_items if list_items else '<p>No blog posts found.</p>'}
        </div>

        <hr style="margin: 2.5rem 0;">

        <h2>Reflections & Quotes</h2>
        <div id="quotes-section">
            {quotes_html if quotes_html else '<p>No quotes found in quotes/quotes.md.</p>'}
        </div>
        <a href="quotes/quotes.html" class="quotes-link">View full quotes page →</a>
    </main>
</body>
</html>"""
    
    with open(os.path.join(ROOT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(main_index)
    print("Build finished successfully.")
    with open(os.path.join(ROOT_DIR, "blogs.json"), "w", encoding="utf-8") as f:
        json.dump(blogs, f, indent=2)


if __name__ == "__main__":
    main()

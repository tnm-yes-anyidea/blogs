import os
import re
import subprocess
import json

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXCLUDE_DIRS = {".git", ".github", "io-site", "data", "figures", "calculations", "quotes"}

# Header with MathJax 3 configuration for complete TeX math/macro rendering
PANDOC_HEADER = """<meta name="viewport" content="width=device-width, initial-scale=1.0">
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
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 850px; margin: 40px auto; padding: 0 20px; line-height: 1.6; color: #222; }
div.abstract { background: #f8f9fa; border-left: 4px solid #0066cc; padding: 12px 16px; margin: 20px 0; font-style: italic; }
blockquote { border-left: 4px solid #ccc; margin: 20px 0; padding: 8px 16px; color: #555; background: #fafafa; font-style: italic; }
table { border-collapse: collapse; width: 100%; margin: 20px 0; }
th, td { border: 1px solid #ddd; padding: 10px 14px; text-align: left; }
th { background-color: #f4f4f4; }
pre, code { background: #f4f4f4; padding: 2px 6px; border-radius: 4px; font-family: monospace; }
a { color: #0066cc; text-decoration: none; }
a:hover { text-decoration: underline; }
.title { font-size: 2em; margin-bottom: 0.2em; }
.author { font-weight: bold; color: #555; margin-bottom: 2em; }
.quote-card { background: #f8f9fa; border: 1px solid #ddd; border-radius: 6px; padding: 1.2rem; margin-bottom: 1.5rem; }
.quote-meta { display: flex; justify-content: space-between; font-size: 0.8rem; color: #666; margin-bottom: 0.8rem; }
.quote-body { margin: 0 0 0.8rem 0; font-size: 1.1rem; color: #222; font-style: italic; }
.quote-author { font-size: 0.85rem; color: #555; text-align: right; font-style: italic; }
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

    # Determine explicit reader format for Pandoc
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

        cards.append(f"""
        <article class="quote-card">
            <div class="quote-meta">
                <span>{date}</span>
                <span>{topic}</span>
            </div>
            <blockquote class="quote-body">“{quote}”</blockquote>
            <div class="quote-author">— {author}</div>
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

    list_items = "".join([f'<li><a href="{b["path"]}">{b["title"]}</a></li>' for b in blogs])
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
    <main>
        <h1>Articles & Research Papers</h1>
        <ul>{list_items if list_items else '<li>No blog posts found.</li>'}</ul>

        <hr style="margin: 2.5rem 0; border: 0; border-top: 1px solid #ddd;">

        <h2>Reflections & Quotes</h2>
        <div id="quotes-section">
            {quotes_html if quotes_html else '<p style="color: #666;">No quotes found in quotes/quotes.md.</p>'}
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

import os
import re
import subprocess
import json

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXCLUDE_DIRS = {".git", ".github", "SCRIPTS", "data", "figures", "calculations", "quotes"}

# Integrated CSS with multiple themes including Solarized
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

:root, [data-theme="warm"] {
    --bg: #f4ebd0;
    --card-bg: #e8dcbe;
    --text: #2b251f;
    --muted: #736454;
    --border: #d8c7a5;
    --accent: #b45309;
    --code-bg: #e2d3b2;
  }

  [data-theme="light"] {
    --bg: #ffffff;
    --card-bg: #f9fafb;
    --text: #111827;
    --muted: #4b5563;
    --border: #e5e7eb;
    --accent: #2563eb;
    --code-bg: #f3f4f6;
  }

  [data-theme="dark"] {
    --bg: #0d1117;
    --card-bg: #161b22;
    --text: #c9d1d9;
    --muted: #8b949e;
    --border: #30363d;
    --accent: #58a6ff;
    --code-bg: #1f242c;
  }

  [data-theme="solarized-light"] {
    --bg: #fdf6e3;
    --card-bg: #eee8d5;
    --text: #657b83;
    --muted: #93a1a1;
    --border: #d5d1c2;
    --accent: #268bd2;
    --code-bg: #e6e0cc;
  }

  [data-theme="solarized-dark"] {
    --bg: #002b36;
    --card-bg: #073642;
    --text: #839496;
    --muted: #586e75;
    --border: #184956;
    --accent: #2aa198;
    --code-bg: #001f27;
  }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Georgia, monospace;
    max-width: 800px;
    margin: 40px auto;
    padding: 0 20px;
    line-height: 1.6;
    transition: background 0.2s ease, color 0.2s ease;
  }

  .nav-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--border);
    padding-bottom: 1rem;
    margin-bottom: 2rem;
  }

  .home-link {
    font-weight: bold;
    font-size: 1rem;
    text-decoration: none;
    color: var(--text);
  }

  .home-link:hover {
    text-decoration: underline;
    color: var(--accent);
  }

  .nav-controls {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .theme-select {
    background: var(--card-bg);
    color: var(--text);
    border: 1px solid var(--border);
    padding: 0.4rem 0.8rem;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.85rem;
  }

  .github-icon {
    width: 22px;
    height: 22px;
    fill: var(--text);
    transition: opacity 0.2s;
  }

  .github-icon:hover { opacity: 0.75; }

  blockquote {
    border-left: 4px solid var(--accent);
    margin: 1rem 0;
    padding: 0.5rem 1rem;
    background: var(--card-bg);
    color: var(--muted);
  }

  code, pre { background: var(--code-bg); padding: 2px 6px; border-radius: 4px; }
  a { color: var(--accent); }
</style>

<header class="nav-header">
  <a href="../index.html" class="home-link">← Back to Index</a>
  <div class="nav-controls">
    <select id="theme-select" class="theme-select" onchange="applyTheme(this.value)">
      <option value="warm">📜 Warm (Sepia)</option>
      <option value="light">☀️ Light</option>
      <option value="dark">🌙 Dark</option>
      <option value="solarized-light">🌅 Solarized Light</option>
      <option value="solarized-dark">🌌 Solarized Dark</option>
    </select>
  </div>
</header>

<script>
  // Dynamic theme switching script
  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('blog-theme', theme);
  }

  document.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('blog-theme') || 'warm';
    applyTheme(savedTheme);
    const select = document.getElementById('theme-select');
    if (select) select.value = savedTheme;
  });
</script>
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
    header_file = os.path.join(ROOT_DIR, "SCRIPTS", "_header.html")
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

        cards.append(f"""
        <article style="margin-bottom: 1.5rem;">
            <div style="display: flex; justify-content: space-between; font-size: 0.85em; opacity: 0.7;">
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

    list_items = "".join([f'<a href="{b["path"]}" class="blog-card"><h3>{b["title"]}</h3></a>' for b in blogs])
    quotes_html = load_quotes()

    main_index = f"""<!DOCTYPE html>
<html lang="en" data-theme="warm">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Blog Index</title>
    {PANDOC_HEADER}
</head>
<body>
    <header class="nav-header">
        <h1 style="margin:0; font-size: 1.5rem;">blogs</h1>
        <div class="nav-controls">
            <select id="theme-select" class="theme-select" onchange="applyTheme(this.value)">
                <option value="warm">📜 Warm (Sepia)</option>
                <option value="light">☀️ Light</option>
                <option value="dark">🌙 Dark</option>
                <option value="solarized-light">🌅 Solarized Light</option>
                <option value="solarized-dark">🌌 Solarized Dark</option>
            </select>
            <a href="https://github.com/tnm-yes-anyidea/blogs" target="_blank" rel="noopener noreferrer" aria-label="GitHub Repository">
                <svg class="github-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
                </svg>
            </a>
        </div>
    </header>

    <main>
        <input type="text" id="search-bar" class="search-box" placeholder="Search articles..." onkeyup="filterArticles()">
        <h2>Articles & Research Papers</h2>
        <div class="blog-grid" id="article-grid">
            {list_items if list_items else '<p>No blog posts found.</p>'}
        </div>

        <hr style="margin: 2.5rem 0; border-color: var(--border);">

        <h2>Reflections & Quotes</h2>
        <div id="quotes-section">
            {quotes_html if quotes_html else '<p>No quotes found in quotes/quotes.md.</p>'}
        </div>
        <a href="quotes/quotes.html">View full quotes page →</a>
    </main>

    <script>
        function filterArticles() {{
            const input = document.getElementById('search-bar').value.toLowerCase();
            const cards = document.querySelectorAll('#article-grid .blog-card');
            cards.forEach(card => {{
                const title = card.textContent.toLowerCase();
                card.style.display = title.includes(input) ? 'block' : 'none';
            }});
        }}
    </script>
</body>
</html>"""
    
    with open(os.path.join(ROOT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(main_index)
    print("Build finished successfully.")
    with open(os.path.join(ROOT_DIR, "blogs.json"), "w", encoding="utf-8") as f:
        json.dump(blogs, f, indent=2)

if __name__ == "__main__":
    main()

import os
import re
import json

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_DIR = os.path.join(ROOT_DIR, "io-site")
EXCLUDE_DIRS = {".git", ".github", "io-site", "data", "figures", "calculations"}

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/contrib/auto-render.min.js"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; line-height: 1.6; color: #222; }}
        pre {{ background: #f4f4f4; padding: 12px; overflow-x: auto; border-radius: 4px; }}
        code {{ font-family: monospace; }}
        .back-link {{ display: inline-block; margin-bottom: 20px; text-decoration: none; color: #0066cc; }}
    </style>
</head>
<body>
    <a href="../index.html" class="back-link">← Back to Index</a>
    <div id="content"></div>

    <script>
        const rawContent = {raw_content_json};
        const fileType = "{file_type}";

        document.addEventListener("DOMContentLoaded", () => {{
            const container = document.getElementById("content");
            
            if (fileType === "md") {{
                container.innerHTML = marked.parse(rawContent);
            }} else {{
                // Escape simple TeX wrappers for HTML display
                let cleanTex = rawContent
                    .replace(/\\\\documentclass.*?\n/g, '')
                    .replace(/\\\\usepackage.*?\n/g, '')
                    .replace(/\\\\begin\\{{document\\}}/g, '')
                    .replace(/\\\\end\\{{document\\}}/g, '')
                    .replace(/\\\\title\\{{(.*?)\\}}/g, '<h1>$1</h1>')
                    .replace(/\\\\section\\{{(.*?)\\}}/g, '<h2>$1</h2>')
                    .replace(/\\\\subsection\\{{(.*?)\\}}/g, '<h3>$1</h3>');
                container.innerHTML = cleanTex;
            }}

            // Render LaTeX Math equations using KaTeX
            renderMathInElement(document.body, {{
                delimiters: [
                    {{left: "$$", right: "$$", display: true}},
                    {{left: "\\[", right: "\\]", display: true}},
                    {{left: "$", right: "$", display: false}},
                    {{left: "\\(", right: "\\)", display: false}}
                ]
            }});
        }});
    </script>
</body>
</html>
"""

def extract_title(content, file_type):
    if file_type == "md":
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        return match.group(1).strip() if match else "Untitled Blog"
    else:
        match = re.search(r"\\title\{([^}]+)\}", content)
        return match.group(1).replace("\\textbf{", "").replace("}", "").strip() if match else "Untitled Paper"

def build_site():
    blogs = []
    
    for entry in os.listdir(ROOT_DIR):
        full_path = os.path.join(ROOT_DIR, entry)
        if os.path.isdir(full_path) and entry not in EXCLUDE_DIRS:
            target_file = None
            file_type = None
            
            for fname in ["paper.md", "README.md", "paper.tex"]:
                fpath = os.path.join(full_path, fname)
                if os.path.exists(fpath):
                    target_file = fpath
                    file_type = "md" if fname.endswith(".md") else "tex"
                    break
            
            if target_file:
                with open(target_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                title = extract_title(content, file_type)
                out_html_path = os.path.join(full_path, "index.html")
                
                # Write rendered blog HTML inside sub-directory
                html_rendered = HTML_TEMPLATE.format(
                    title=title,
                    raw_content_json=json.dumps(content),
                    file_type=file_type
                )
                with open(out_html_path, "w", encoding="utf-8") as f:
                    f.write(html_rendered)
                
                blogs.append({"title": title, "path": f"{entry}/index.html"})

    # Generate main index.html
    index_cards = "".join([f'<li><a href="{b["path"]}">{b["title"]}</a></li>' for b in blogs])
    main_index = f"""<!DOCTYPE html>
<html>
<head><title>Blog Index</title></head>
<body>
    <h1>Blog Posts & Research</h1>
    <ul>{index_cards}</ul>
</body>
</html>"""
    
    with open(os.path.join(ROOT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(main_index)

if __name__ == "__main__":
    build_site()
    print("Site built successfully.")

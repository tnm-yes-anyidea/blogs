import os
import re
import subprocess

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXCLUDE_DIRS = {".git", ".github", "io-site", "data", "figures", "calculations"}

PANDOC_HEADER = """<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
<style>
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; line-height: 1.6; color: #222; }
div.abstract { background: #f8f9fa; border-left: 4px solid #0066cc; padding: 12px 16px; margin: 20px 0; }
table { border-collapse: collapse; width: 100%; margin: 20px 0; }
th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: left; }
th { background-color: #f4f4f4; }
pre, code { background: #f4f4f4; padding: 2px 6px; border-radius: 4px; font-family: monospace; }
a { color: #0066cc; text-decoration: none; }
a:hover { text-decoration: underline; }
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
            # Parse LaTeX title tags, stripping formatting like \textbf{}
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

    cmd = [
        "pandoc",
        input_file,
        "-o", output_html,
        "--standalone",
        "--katex",
        f"--metadata=title:{title}",
        "-H", header_file
    ]
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    if os.path.exists(header_file):
        os.remove(header_file)
        
    if res.returncode != 0:
        print(f"Pandoc error on {input_file}:\n{res.stderr}")
        return False
    return True

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

    # Create root index.html
    list_items = "".join([f'<li><a href="{b["path"]}">{b["title"]}</a></li>' for b in blogs])
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
    </main>
</body>
</html>"""
    
    with open(os.path.join(ROOT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(main_index)
    print("Build finished successfully.")

if __name__ == "__main__":
    main()

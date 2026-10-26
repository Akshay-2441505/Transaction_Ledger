with open("static/index.html", "r", encoding="utf-8") as f:
    html = f.read()

with open("static/css/dashboard.css", "r", encoding="utf-8") as f:
    css = f.read()

with open("static/js/dashboard.js", "r", encoding="utf-8") as f:
    js = f.read()

target_css = '<link rel="stylesheet" href="/static/css/dashboard.css">'
replacement_css = f"<style>\n{css}\n</style>"

target_js = '<script src="/static/js/dashboard.js"></script>'
replacement_js = f"<script>\n{js}\n</script>"

if target_css in html:
    html = html.replace(target_css, replacement_css)
    print("CSS replaced!")
else:
    print("Warning: target_css not found")

if target_js in html:
    html = html.replace(target_js, replacement_js)
    print("JS replaced!")
else:
    print("Warning: target_js not found")

with open("static/index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Inlining complete!")

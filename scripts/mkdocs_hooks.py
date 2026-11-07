"""Keep the interactive homepage independent of regenerated academic reports."""
def on_page_markdown(markdown, page, config, files):
    if page.file.src_uri == "index.md":
        page.meta["template"] = "lab.html"
        page.meta["title"] = "NYC Taxi ML Lab · The tipping point"
    return markdown

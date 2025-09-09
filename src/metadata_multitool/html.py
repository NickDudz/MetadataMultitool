def html_snippet(img_name: str, alt_text: str, title_text: str) -> str:
    return (
        f'<img src="{img_name}" alt="{alt_text}" title="{title_text}" loading="lazy">'
    )

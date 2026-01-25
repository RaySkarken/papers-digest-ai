from __future__ import annotations

import re
from datetime import date
from typing import Sequence

from papers_digest.models import Paper


def _clean_html(text: str) -> str:
    """Remove HTML tags from text."""
    return re.sub(r"<[^>]+>", "", text)


def _escape_markdown_v2(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2."""
    # Characters that need escaping in MarkdownV2: _ * [ ] ( ) ~ ` > # + - = | { } . !
    # First escape backslashes, then other special chars
    # This avoids double-escaping issues
    text = text.replace("\\", "\\\\")  # Escape backslashes first
    # Then escape all other special characters
    for char in "_*[]()~`>#+-=|{}.!":
        text = text.replace(char, "\\" + char)
    return text


def format_digest(
    query: str,
    target_date: date,
    papers: Sequence[Paper],
    summaries: dict[str, str],
    recommendations: Sequence[str],
) -> list[str]:
    """Format digest as Telegram MarkdownV2 messages. Returns list of message parts."""
    messages = []
    
    # Header - escape all text, translate to Russian
    date_str = _escape_markdown_v2(target_date.isoformat())
    header_text = _escape_markdown_v2("Дайджест статей за")
    header = f"*{header_text} {date_str}*\n\n"
    query_text = _escape_markdown_v2("Область:")
    query_escaped = _escape_markdown_v2(query)
    header += f"{query_text} *{query_escaped}*\n\n"
    
    if not papers:
        no_papers_text = _escape_markdown_v2("Сегодня статей не найдено.")
        header += no_papers_text
        messages.append(header)
        return messages

    top_papers_text = _escape_markdown_v2("Топ статей")
    header += f"*{top_papers_text}*\n\n"
    current_message = header
    
    for idx, paper in enumerate(papers, start=1):
        summary = summaries.get(paper.paper_id, "Краткое содержание недоступно.")
        authors = ", ".join(paper.authors) if paper.authors else "Авторы неизвестны"
        
        # Clean HTML tags and escape all text fields
        title_clean = _clean_html(paper.title)
        title_escaped = _escape_markdown_v2(title_clean)
        authors_clean = _clean_html(authors)
        authors_escaped = _escape_markdown_v2(authors_clean)
        summary_clean = _clean_html(summary)
        summary_escaped = _escape_markdown_v2(summary_clean)
        source_escaped = _escape_markdown_v2(paper.source)
        
        # Format paper entry - escape all labels, translate to Russian
        paper_entry = f"{idx}\\. *{title_escaped}*\n"
        source_label = _escape_markdown_v2("Источник:")
        paper_entry += f"   {source_label} {source_escaped}\n"
        authors_label = _escape_markdown_v2("Авторы:")
        paper_entry += f"   {authors_label} {authors_escaped}\n"
        if paper.url:
            link_label = _escape_markdown_v2("Ссылка:")
            url_escaped = _escape_markdown_v2(paper.url)
            paper_entry += f"   {link_label} {url_escaped}\n"
        summary_label = _escape_markdown_v2("Краткое содержание:")
        paper_entry += f"   {summary_label} {summary_escaped}\n\n"
        
        # Check if adding this paper would exceed 4096 characters
        if len(current_message) + len(paper_entry) > 4000:  # Leave some margin
            messages.append(current_message.rstrip())
            current_message = ""
        
        current_message += paper_entry
    
    if current_message.strip():
        messages.append(current_message.rstrip())
    
    return messages if messages else [header]


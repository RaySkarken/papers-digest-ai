from __future__ import annotations

from datetime import date
from typing import Sequence

from papers_digest.models import Paper


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
    
    # Header - escape all text
    date_str = _escape_markdown_v2(target_date.isoformat())
    header_text = _escape_markdown_v2("Papers digest for")
    header = f"*{header_text} {date_str}*\n\n"
    query_text = _escape_markdown_v2("Query:")
    query_escaped = _escape_markdown_v2(query)
    header += f"{query_text} *{query_escaped}*\n\n"
    
    if not papers:
        no_papers_text = _escape_markdown_v2("No papers matched today.")
        header += no_papers_text
        messages.append(header)
        return messages

    top_papers_text = _escape_markdown_v2("Top papers")
    header += f"*{top_papers_text}*\n\n"
    current_message = header
    
    for idx, paper in enumerate(papers, start=1):
        summary = summaries.get(paper.paper_id, "Summary not available.")
        authors = ", ".join(paper.authors) if paper.authors else "Unknown authors"
        
        # Escape all text fields
        title_escaped = _escape_markdown_v2(paper.title)
        authors_escaped = _escape_markdown_v2(authors)
        summary_escaped = _escape_markdown_v2(summary)
        source_escaped = _escape_markdown_v2(paper.source)
        
        # Format paper entry - escape all labels
        paper_entry = f"{idx}\\. *{title_escaped}*\n"
        source_label = _escape_markdown_v2("Source:")
        paper_entry += f"   {source_label} {source_escaped}\n"
        authors_label = _escape_markdown_v2("Authors:")
        paper_entry += f"   {authors_label} {authors_escaped}\n"
        if paper.url:
            # URLs in MarkdownV2 should be formatted as [text](url)
            link_label = _escape_markdown_v2("Link:")
            # Escape URL but keep it as plain text for now
            url_escaped = _escape_markdown_v2(paper.url)
            paper_entry += f"   {link_label} {url_escaped}\n"
        summary_label = _escape_markdown_v2("Summary:")
        paper_entry += f"   {summary_label} {summary_escaped}\n\n"
        
        # Check if adding this paper would exceed 4096 characters
        if len(current_message) + len(paper_entry) > 4000:  # Leave some margin
            messages.append(current_message.rstrip())
            current_message = ""
        
        current_message += paper_entry

    # Add recommendations if any
    if recommendations:
        recommendations_label = _escape_markdown_v2("Recommendations")
        recommendations_text = f"\n*{recommendations_label}*\n\n"
        for item in recommendations:
            item_escaped = _escape_markdown_v2(item)
            bullet = _escape_markdown_v2("•")
            recommendations_text += f"{bullet} {item_escaped}\n"
        
        if len(current_message) + len(recommendations_text) > 4000:
            messages.append(current_message.rstrip())
            current_message = recommendations_text
        else:
            current_message += recommendations_text
    
    if current_message.strip():
        messages.append(current_message.rstrip())
    
    return messages if messages else [header]


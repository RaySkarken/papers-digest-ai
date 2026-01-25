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
    
    # Header - escape date
    date_str = _escape_markdown_v2(target_date.isoformat())
    header = f"*Papers digest for {date_str}*\n\n"
    header += f"Query: *{_escape_markdown_v2(query)}*\n\n"
    
    if not papers:
        header += _escape_markdown_v2("No papers matched today.")
        messages.append(header)
        return messages

    header += "*Top papers*\n\n"
    current_message = header
    
    for idx, paper in enumerate(papers, start=1):
        summary = summaries.get(paper.paper_id, "Summary not available.")
        authors = ", ".join(paper.authors) if paper.authors else "Unknown authors"
        
        # Escape all text fields
        title_escaped = _escape_markdown_v2(paper.title)
        authors_escaped = _escape_markdown_v2(authors)
        summary_escaped = _escape_markdown_v2(summary)
        source_escaped = _escape_markdown_v2(paper.source)
        
        # Format paper entry
        paper_entry = f"{idx}\\. *{title_escaped}*\n"
        paper_entry += f"   Source: {source_escaped}\n"
        paper_entry += f"   Authors: {authors_escaped}\n"
        if paper.url:
            # URLs don't need escaping in MarkdownV2, but we need to format them properly
            paper_entry += f"   Link: {paper.url}\n"
        paper_entry += f"   Summary: {summary_escaped}\n\n"
        
        # Check if adding this paper would exceed 4096 characters
        if len(current_message) + len(paper_entry) > 4000:  # Leave some margin
            messages.append(current_message.rstrip())
            current_message = ""
        
        current_message += paper_entry

    # Add recommendations if any
    if recommendations:
        recommendations_text = "\n*Recommendations*\n\n"
        for item in recommendations:
            item_escaped = _escape_markdown_v2(item)
            recommendations_text += f"• {item_escaped}\n"
        
        if len(current_message) + len(recommendations_text) > 4000:
            messages.append(current_message.rstrip())
            current_message = recommendations_text
        else:
            current_message += recommendations_text
    
    if current_message.strip():
        messages.append(current_message.rstrip())
    
    return messages if messages else [header]


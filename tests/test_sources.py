from datetime import date

import responses

from papers_digest.sources.arxiv import ArxivSource
from papers_digest.sources.crossref import CrossrefSource
from papers_digest.sources.semantic_scholar import SemanticScholarSource


@responses.activate
def test_arxiv_source_filters_by_date():
    query = "graph"
    target = date(2025, 1, 1)
    url = (
        "http://export.arxiv.org/api/query?"
        f"search_query=all:{query}&sortBy=submittedDate&sortOrder=descending&max_results=50"
    )
    xml = """
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <title>Graph paper</title>
        <id>http://arxiv.org/abs/1234</id>
        <updated>2025-01-01T00:00:00Z</updated>
        <published>2025-01-01T00:00:00Z</published>
        <summary>Graph summary</summary>
        <author><name>Alice</name></author>
      </entry>
    </feed>
    """
    responses.add(responses.GET, url, body=xml, status=200)

    source = ArxivSource(max_results=50)
    papers = list(source.search(query, target))
    assert len(papers) == 1
    assert papers[0].source == "arXiv"


@responses.activate
def test_crossref_source_filters_by_date():
    query = "graph"
    target = date(2025, 1, 1)
    url = (
        "https://api.crossref.org/works?"
        f"query={query}&rows=50&filter=from-pub-date:2025-01-01,until-pub-date:2025-01-01"
    )
    payload = {
        "message": {
            "items": [
                {
                    "title": ["Graph paper"],
                    "URL": "http://example.com",
                    "issued": {"date-parts": [[2025, 1, 1]]},
                }
            ]
        }
    }
    responses.add(responses.GET, url, json=payload, status=200)

    source = CrossrefSource(rows=50)
    papers = list(source.search(query, target))
    assert len(papers) == 1
    assert papers[0].source == "Crossref"


@responses.activate
def test_semantic_scholar_source_filters_by_date():
    query = "graph"
    target = date(2025, 1, 1)
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    payload = {
        "data": [
            {
                "title": "Graph paper",
                "url": "http://example.com",
                "publicationDate": "2025-01-01",
                "authors": [{"name": "Alice"}],
                "abstract": "Graph summary",
            }
        ]
    }
    responses.add(responses.GET, url, json=payload, status=200)

    source = SemanticScholarSource(limit=50)
    papers = list(source.search(query, target))
    assert len(papers) == 1
    assert papers[0].source == "Semantic Scholar"

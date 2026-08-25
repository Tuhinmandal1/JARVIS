from ddgs import DDGS


def web_search(query: str, max_results: int = 5) -> str:
    """
    Search the web and return a short summary of the top results.

    Args:
        query: What to search for.
        max_results: How many results to include (default 5).

    Returns:
        A formatted string of results (title, snippet, url).
    """
    query = query.strip()

    if not query:
        return "I need something to search for."

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
    except Exception as error:
        return f"Web search failed: {error}"

    if not results:
        return f"No results found for '{query}'."

    lines = []
    for i, r in enumerate(results, start=1):
        title = r.get("title", "Untitled")
        snippet = r.get("body", "")
        url = r.get("href", "")
        lines.append(f"{i}. {title} — {snippet} ({url})")

    return "\n".join(lines)

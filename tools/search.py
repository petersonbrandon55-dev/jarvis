from config.settings import TAVILY_API_KEY


def web_search(query: str, max_results: int = 5) -> str:
    if not TAVILY_API_KEY:
        return "Tavily API key not set. Add TAVILY_API_KEY to .env to enable web search."

    from tavily import TavilyClient
    client = TavilyClient(api_key=TAVILY_API_KEY)
    results = client.search(query=query, max_results=max_results)

    output = []
    for r in results.get("results", []):
        output.append(f"**{r['title']}**\n{r['url']}\n{r.get('content', '')[:400]}")
    return "\n\n".join(output) if output else "No results found."

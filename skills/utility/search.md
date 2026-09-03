# Skill: Web Search

## Trigger

- The request requires current information such as news, prices, or real-time data.
- The user explicitly asks to search or look something up.
- Claude cannot answer accurately from its training data.
- A generation prompt needs current reference material.

---

## Tool

**Brave Search API**

- Required key: `SEARCH_API_KEY`
- Call: MCP tool `search(query, count)`

---

## Procedure

1. **Refine the query:** Turn the user's intent into precise search terms.
2. **Call the API:** Send the query to Brave Search.
3. **Filter results:** Extract titles, snippets, and URLs from the top N results.
4. **Synthesize:** Answer the question from the results or inject key information into a generation prompt.

---

## Integration with Other Skills

- Use search results as source content for PowerPoint, Word, PDF, or Excel generation.
- Use descriptions of reference images to improve image-generation prompts.

---

## Error Handling

| Error | Handling |
|-------|----------|
| API key not configured | Ask the user to set `SEARCH_API_KEY` and explain that web search is unavailable |
| No results | Tell the user and retry with different terms |
| Network timeout | Retry once; if it still fails, notify the user |

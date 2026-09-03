# Skill: Web Browsing

## Trigger

- The user supplies a URL and asks to read the page.
- A search result needs deeper retrieval of its full content.
- A generation task must use a webpage as a reference.

---

## Tool

**Playwright** local browser automation; no API key required.

- Call: MCP tool `browse(url, max_chars=6000)`
- The tool waits for network idle, supporting asynchronously rendered SPA detail pages such as jobs and product listings. If the first extraction is too short, it scrolls and retries with backoff up to four times instead of failing immediately on an empty shell.

---

## Procedure

1. **Validate the URL:** Confirm it is valid and explicitly supplied by the user.
2. **Load the page:** Call `browse(url)`; the tool handles JavaScript rendering waits and retries.
3. **Check the result:**
   - `warning` is `null`: extraction succeeded; use `content`.
   - `warning` is non-empty because content remains too short: likely a login wall or anti-bot block. Follow the error handling below and **do not** declare failure based only on the first attempt.
   - `truncated` is `true`: if the user needs more, call once more with larger `max_chars` rather than reporting incomplete content immediately.
4. **Return content:** Provide `content` as Markdown for answering the user or preparing a generation task.

---

## Error Handling

| Error | Handling |
|-------|----------|
| Playwright is not installed | Ask the user to run `pip install playwright && playwright install` |
| `warning` says content remains too short | Retry once with larger `max_chars`; if it still fails, explain that the page may have a login wall or strong anti-bot protection and ask for copied text or screenshots |
| Login/paywall required | Explain that restricted content is inaccessible and ask for page text or screenshots from an authenticated session |
| Invalid URL | Report the error and ask the user to confirm the URL |

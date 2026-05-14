# Spec: Application Hardening and UI Polish

## Objective
Improve the Streamlit exploration app so it is safer with external data, clearer on mobile, and easier to maintain without changing the core plant/animal discovery flow.

## Tech Stack
Python, Streamlit, requests, optional OpenCC conversion, custom CSS.

## Commands
Build check: `C:\Users\jeff2\anaconda3\python.exe -m compileall app.py api_handler.py config.py tests`
Test: `C:\Users\jeff2\anaconda3\python.exe -m unittest discover -s tests`
Dev: `C:\Users\jeff2\anaconda3\Scripts\streamlit.exe run app.py`

## Project Structure
Root Python files contain the Streamlit UI, API integration, and config.
`style.css` contains Streamlit-specific presentation rules.
`tests/` contains focused unit tests for safety-critical helpers and API behavior.

## Code Style
Keep external API concerns inside `api_handler.py`, configuration inside `config.py`, and Streamlit rendering helpers inside `app.py`.

```python
def safe_text(value, default="N/A"):
    return escape(str(value if value not in (None, "") else default), quote=True)
```

## Testing Strategy
Use small `unittest` tests for API boundaries, failure behavior, and HTML escaping. Browser/manual verification is required for visual camera layout changes because Streamlit generates the final DOM at runtime.

## Boundaries
- Always: validate uploaded files, escape external text before HTML rendering, use request timeouts, keep secrets out of source.
- Ask first: add new third-party services, change API providers, add runtime dependencies.
- Never: commit API keys, expose raw exception details to users, render external content without escaping.

## Success Criteria
- No hardcoded PlantNet API key remains.
- Unsupported/empty/oversized uploads are rejected before network calls.
- PlantNet and Wikipedia requests use timeouts and safe error messages.
- User-facing HTML content is escaped.
- Mobile camera controls have responsive sizing and visible focus states.
- Unit tests and compile checks pass.

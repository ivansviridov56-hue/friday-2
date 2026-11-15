# Progress

## Done
- [x] Stage 0: foundation
  - Python 3.11.9, git, VS Code, .venv, pytest
  - Skeleton + smoke tests (2 passed)
  - CLAUDE.md, HANDOFF.md, PROGRESS.md, README (en/ru), LICENSE (MIT)
  - Public repo: https://github.com/ivansviridov56-hue/friday-2
  - GitHub Actions runs pytest on every push (green)
- [x] Stage 1a: probe tools (probe.py, scan.py, catalog.py, cf_probe.py), 19 tests
    - [x] Free LLM sources reachable from Belarus without VPN: Cloudflare Workers AI
      (460-800 ms), OpenRouter free models (limited daily quota)
    - [x] Not available: Groq, Cerebras, NVIDIA (phone check), Mistral (paid), Gemini (no VPN)

## Next
Stage 1b: quality test of Russian answers on 3 Cloudflare models
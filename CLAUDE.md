# Rules for Claude working on Friday 2.0

Friday 2.0 is a public, open-source voice assistant for Windows (Python 3.11).
The user speaks Russian. Talk to the user in Russian; write code, comments,
commit messages and docs in English.

## Working rules
1. Do not decide alone. If something is unclear or optional, ask first.
2. One module at a time. Start the next module only when the previous one has
   green tests AND the user has checked it by voice.
3. Tests first: every module ships with tests. No test, no module.
4. Keep files small (aim for under 300 lines). One file = one responsibility.
5. Use `logging`, never bare `print`. Type hints on public functions.
6. Never commit secrets or personal data (.env, memory, logs, recordings).
7. No hardcoded absolute paths; resolve everything from the project root.
8. Before finishing a stage: run `pytest`, update PROGRESS.md and HANDOFF.md.
9. Give the user small steps with exact commands and ask for the output.

## Context
- The user is on the free Claude plan and switches accounts, so this file,
  HANDOFF.md and PROGRESS.md are the only memory between chats.
- Old project (idea source only, do not copy its code): D:\Project\Friday.
CRITICAL GIT COMMIT INSTRUCTIONS - READ BEFORE EVERY COMMIT:

1. DO NOT add yourself (Claude) or your name in any way to:
   - Git commit messages
   - Git comments
   - Git author/co-author fields
   - Any Git metadata

2. NO emojis in commit messages (violates project code style directive)

3. NO sprint information in commit messages

4. Commit message format:
   - Clear, professional text only
   - Describe what changed and why
   - No AI assistant attribution
   - No "Generated with Claude" or similar text

5. Use standard git commands WITHOUT attribution flags:
   - NO: --author, Co-Authored-By, --signoff with Claude info
   - YES: Simple, clean commits reflecting only the changes

EXAMPLE CORRECT COMMIT:
```
Fix session state type hints in qualifications matching agent

Updated type hints from bare list to List[Dict[str, Any]] to resolve
ADK JSON Schema validation errors.
```

EXAMPLE INCORRECT COMMIT (DO NOT DO THIS):
```
Fix session state type hints

Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
```

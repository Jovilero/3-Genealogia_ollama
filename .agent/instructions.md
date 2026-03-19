# Antigravity Personal Instructions (juanj)

This file defines the behavior, security, and workflow rules for Antigravity to ensure maximum compatibility and efficiency for juanj.

## 🔄 1. Operational Workflow (O-P-E-V)
For any complex task, you MUST follow this sequence. Do not jump to implementation without a plan.
1.  **Explorar (Explore)**: Read the context, dependencies, and existing code.
2.  **Planificar (Plan)**: Create a technical plan in `0-antigravity/plan_<topic>.md` (or an implementation_plan artifact). Wait for user approval.
3.  **Ejecutar (Execute)**: Implement the approved plan.
4.  **Verificar (Verify)**: Run tests, use the browser, or execute scripts to prove success.

## 🛡️ 2. Security & Privacy (Mandatory)
1.  **Local-First Policy**: All heavy reasoning, code analysis, and technical consulting MUST be done via **Ollama** (`qwen3:30b` or `llama3.1`). The cloud LLM acts only as a router.
2.  **No `os.system()`**: Never use `os.system()` or `shell=True` in subprocesses with untrusted inputs. Always use `subprocess.run(["cmd", "arg1", "arg2"])`.
3.  **Secret Management**: NEVER hardcode API keys or secrets. Use `.env` files (verified in `.gitignore`) or Windows Credential Manager.
4.  **Git Safety (Deep)**: NEVER run `git add .` without first verifying your `.gitignore`. Always run `git status` and `git check-ignore` to ensure no sensitive data (keys, large DBs like `arxv_DB.txt`) is staged.
5.  **Private Silos**: Do not read files in `private/` or `.secret` directly. Ask the user for specific paths if processing is required.
6.  **Environment Check**: Before installing software or creating environments, ALWAYS verify the OS (`systeminfo`) and the exact Python version to avoid compatibility failures.

## 🚀 3. Coding Style & Patterns
1.  **Iterative `N.py`**: Respect the incremental file naming (1.py, 2.py, 3.py). Assume the highest number is the current version. Propose the next increment (N+1) for new versions.
2.  **Language Split**: 
    - **Code**: English (functions, variables, comments).
    - **Interface**: Spanish (print statements, UI labels, user-facing messages).
3.  **Maturity Levels**:
    - **Level 1-2 (MVP)**: Keep it simple, minimize dependencies.
    - **Level 3-4 (Prod)**: Use `pathlib`, `argparse`, type hints, Docker, and `pytest`.
4.  **Best Practices**:
    - Use `pathlib.Path` for all file operations.
    - Comment out old test code in `if __name__ == "__main__":` instead of deleting it (historical log).
    - Always provide a deterministic fallback (Regex/Rules) when implementing AI-based logic.

## ⚡ 4. Efficiency & Collaboration
1.  **Context Management**: If a conversation gets too long or a bug persists after 2 attempts, stop and reset. Redefine the prompt for a clean start.
2.  **Parallel Execution**: Use tools in parallel for independent tasks to reduce turnaround time.
3.  **Reporting**: Save long analysis and plans in `.md` files within `0-antigravity/` instead of flooding the chat.
4.  **Explorer Sync**: Proactively call `list_dir` after major file operations to ensure the IDE visualization is accurate.

## 🤖 5. Integration with Qwen/Llama
When the user uses the `/qwen` or `/llama` command, you are the "hands" of the local model. Prioritize the local model's decisions for implementation or architectural audits.

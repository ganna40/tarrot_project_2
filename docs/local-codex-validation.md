# Local Codex Subscription Validation

This mode is for local quality testing only. The deterministic Tarot Engine still decides the context, score, verdict, card flow, and advice constraints. The locally authenticated Codex CLI only turns that plan into natural Korean.

## Flow

```text
FastAPI request
  -> PostgreSQL/SQLite curated Tarot knowledge
  -> deterministic rule engine
  -> InterpretationPlan
  -> local `codex exec`
  -> ChatGPT/Codex subscription
  -> Korean wording
```

The application never reads or stores ChatGPT credentials. Authentication belongs to the Codex CLI.

## 1. Verify Codex authentication

PowerShell:

```powershell
codex --version
codex login status
```

If login is required:

```powershell
codex login
```

## 2. Start the Tarot backend with the subscription provider

From the repository root on Windows:

```powershell
git checkout new
git pull
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\run_codex_local.ps1
```

This script:

- checks the Codex CLI and login state
- creates `.venv` when needed
- installs backend dependencies
- sets `LLM_PROVIDER=codex_subscription`
- uses a local SQLite validation DB (`tarot-local.db`)
- starts FastAPI at `http://127.0.0.1:8000`

Do not use Docker for this validation mode unless the container is explicitly given the Codex CLI and authentication state. The supplied script intentionally runs FastAPI on the host so it can reuse the host Codex login.

Optional model override before starting:

```powershell
$env:CODEX_MODEL="<a model available to your Codex account>"
.\scripts\run_codex_local.ps1
```

If `CODEX_MODEL` is empty, Codex CLI uses its configured/default model.

## 3. Run the representative smoke test

Keep the backend terminal open. In a second PowerShell window:

```powershell
cd <repository-path>
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\test_codex_local.ps1
```

The representative reading is:

```text
Question: 게임을 만들면 실제 투자로 이어질까?
Cards: Ten of Swords -> Eight of Wands -> The Hierophant
Context: BUSINESS
```

Success criteria:

```text
HTTP 200
llm_used = true
verdict/score/flow_summary are produced by the deterministic engine
overall_interpretation is written by local Codex
```

## 4. Compare Codex wording against the rule-only result

For a stricter quality check, send the same request twice:

- `use_llm=false`: deterministic fallback wording
- `use_llm=true`: local Codex wording

The following fields must remain identical:

```text
reading_context
verdict
score
flow_summary
```

Only the natural-language wording should improve.

## Safety boundary

The Codex adapter runs one-shot commands with:

```text
codex exec
--ephemeral
--sandbox read-only
--ask-for-approval never
--skip-git-repo-check
```

It also runs in a fresh temporary working directory. The prompt explicitly says that no file or tool use is required. This keeps the local validation path focused on wording rather than code/file operations and prevents an unattended request from waiting for an approval prompt.

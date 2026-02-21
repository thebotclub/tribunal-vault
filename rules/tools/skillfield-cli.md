## Skillfield CLI Reference

The `skillfield` binary is at `~/.skillfield/bin/skillfield`. These are **all** available commands — do NOT call commands that aren't listed here.

### Session & Context

| Command | Purpose | Example |
|---------|---------|---------|
| `skillfield` | Start Claude with Endless Mode (primary entry point) | Just type `skillfield` or `sfc` |
| `skillfield run [args...]` | Start with optional flags | `skillfield run --skip-update-check` |
| `skillfield check-context --json` | Get context usage percentage | Returns `{"status": "OK", "percentage": 47.0}` or `{"status": "CLEAR_NEEDED", ...}` |
| `skillfield send-clear <plan.md>` | Trigger Endless Mode continuation with plan | `skillfield send-clear docs/plans/2026-02-11-foo.md` |
| `skillfield send-clear --general` | Trigger continuation without plan | Only when no active plan exists |
| `skillfield register-plan <path> <status>` | Associate plan with current session | `skillfield register-plan docs/plans/foo.md PENDING` |

### Worktree Management

| Command | Purpose | JSON Output |
|---------|---------|-------------|
| `skillfield worktree detect --json <slug>` | Check if worktree exists | `{"found": true, "path": "...", "branch": "...", "base_branch": "..."}` |
| `skillfield worktree create --json <slug>` | Create worktree AND register with session | `{"path": "...", "branch": "spec/<slug>", "base_branch": "main"}` |
| `skillfield worktree diff --json <slug>` | List changed files in worktree | JSON with file changes |
| `skillfield worktree sync --json <slug>` | Squash merge worktree to base branch | `{"success": true, "files_changed": N, "commit_hash": "..."}` |
| `skillfield worktree cleanup --json <slug>` | Remove worktree and branch | Deletes worktree directory and git branch |
| `skillfield worktree status --json` | Show active worktree info | `{"active": false}` or `{"active": true, ...}` |

**Slug** = plan filename without date prefix and `.md` (e.g., `2026-02-11-add-auth.md` → `add-auth`).

**Error handling:** `create` returns `{"success": false, "error": "dirty", "detail": "..."}` when the working tree has uncommitted changes. Use `AskUserQuestion` to let the user choose: commit, stash, or skip worktree (see spec-implement Step 2.1b).

### Access & Auth

| Command | Purpose |
|---------|---------|
| `skillfield activate <key> [--json]` | Activate access on this machine |
| `skillfield deactivate` | Deactivate access on this machine |
| `skillfield status [--json]` | Show access and session status |
| `skillfield verify [--json]` | Verify access authorization (used by hooks) |
| `skillfield trial --check [--json]` | Check access eligibility |
| `skillfield trial --start [--json]` | Start access verification |

### Skills Management

| Command | Purpose | Example |
|---------|---------|---------|
| `skillfield skills` | List all project skills (default) | `sfc skills` |
| `skillfield skills list` | List all project skills | `sfc skills list` |
| `skillfield skills show <name>` | Display a skill's content | `sfc skills show deploy-workflow` |
| `skillfield skills init` | Bootstrap .claude/ with project config | `sfc skills init` |
| `skillfield skills analyze` | AI-powered codebase analysis (headless /sync) | `sfc skills analyze` |
| `skillfield skills analyze --dry-run` | Preview analysis without running | `sfc skills analyze --dry-run` |
| `skillfield skills create <name>` | Create skill from template (kebab-case) | `sfc skills create api-client` |
| `skillfield skills doctor` | Validate skill files for issues | `sfc skills doctor` |

### Other

| Command | Purpose |
|---------|---------|
| `skillfield greet [--name NAME] [--json]` | Print welcome banner |
| `skillfield statusline` | Format status bar (reads JSON from stdin, used by Claude Code settings) |

### Commands That Do NOT Exist

Do NOT attempt these — they will fail:
- ~~`skillfield pipe`~~ — Never implemented
- ~~`skillfield update`~~ — Auto-update is built into `skillfield run`

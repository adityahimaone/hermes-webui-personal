# Persistent Remote Spaces Implementation Plan

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** Make WebUI spaces authoritative execution targets so Kanban tasks selected for `Remote MAC SAAS` run through `mac-tailscale` on the Mac and reuse the same stable space target.

**架构：** Extend the existing WebUI workspace registry with stable IDs and transport metadata. Send a space ID through the create-task API, resolve it into an immutable task execution snapshot, and make Kanban worker startup consume that snapshot instead of inferring from local-looking paths. Remote execution fails closed.

**技术栈：** Python stdlib, SQLite, existing Hermes SSH terminal backend, vanilla JavaScript, pytest.

---

## Files and responsibilities

- Modify `api/workspace.py`: normalize legacy workspace entries, expose stable space records, validate remote metadata.
- Modify `api/kanban_bridge.py`: accept `space_id`, resolve the registered space, stop remote-path downgrade, pass snapshot fields to Kanban DB.
- Modify `static/index.html`, `static/panels.js`, `static/i18n.js`: select a registered space in create modal and submit its ID.
- Modify `/home/adityahimaone/.hermes/hermes-agent/hermes_cli/kanban_db.py`: nullable space/snapshot fields, schema migration, task serialization, task creation/lookup, and replace its duplicate remote-path-to-scratch guard.
- Modify `/home/adityahimaone/.hermes/hermes-agent/hermes_cli/kanban.py`: CLI display and workspace resolution integration.
- Modify `/home/adityahimaone/.hermes/hermes-agent/tools/kanban_tools.py`: create/detail payload parity for tool-created tasks.
- Modify the Kanban worker spawn path in `/home/adityahimaone/.hermes/hermes-agent/hermes_cli/kanban_db.py` (dispatch loop/spawn environment): consume snapshot transport and remote cwd; preserve local behavior. If execution is delegated into a helper, update that exact helper only after call-graph confirmation.
- Add/update tests beside existing workspace, bridge, Kanban DB, worker terminal, and worktree tests.
- Add implementation documentation only where runtime contract changes; do not edit `CHANGELOG.md`.

## Task 1: WebUI space normalization and API contract

- [ ] Write failing tests for legacy `{path,name}` normalization, stable IDs, local default transport, and explicit SSH record for `Remote MAC SAAS`.
- [ ] Run focused WebUI tests through `./scripts/test.sh`; confirm failures show missing stable-space behavior.
- [ ] Implement minimal normalization in `api/workspace.py`; preserve existing list/read/write behavior and avoid storing credentials.
- [ ] Run focused tests; confirm pass.
- [ ] Commit only workspace model/tests.

## Task 2: Kanban bridge must preserve selected remote space

- [ ] Write failing regression tests for POST task creation with `space_id=remote-mac-saas`; assert returned task contains SSH transport and `mac-tailscale`, not `scratch` downgrade. Include `t_5dd6c5f3` field shape as regression input.
- [ ] Run focused tests and confirm current line-346 downgrade causes failure.
- [ ] Add bridge resolver using canonical WebUI space records. Reject unknown IDs and invalid transport/path; never infer remote from path prefixes.
- [ ] Pass resolved snapshot fields into `kb.create_task`.
- [ ] Run bridge regression tests; confirm pass.
- [ ] Commit bridge/tests.

## Task 3: Kanban DB persistence and backward compatibility

- [ ] Write failing DB tests for schema creation/migration, round-trip of `space_id`, transport, SSH target, remote path, and legacy task reads.
- [ ] Run focused DB tests; confirm missing columns/arguments fail.
- [ ] Add nullable fields or serialized snapshot using existing migration pattern; update `Task`, row conversion, create/update/read paths, and task dicts.
- [ ] Keep tasks without space metadata on existing local/scratch path.
- [ ] Run DB and neighboring Kanban tests; confirm pass.
- [ ] Commit DB/tests.

## Task 4: Worker routing and remote worktree execution

- [ ] Write failing worker tests with two tasks (local and SSH) asserting resolved execution backend/cwd; assert SSH preflight failure blocks instead of local fallback.
- [ ] Run focused worker tests and confirm current worker ignores snapshot transport.
- [ ] Update workspace resolution/spawn environment at the smallest shared chokepoint. Local keeps current behavior; SSH uses allowlisted `mac-tailscale` and target-side cwd.
- [ ] Include explicit execution metadata in worker prompt/context without secrets.
- [ ] Ensure worktree creation uses remote target for SSH spaces and returns one consistent path for subsequent commands.
- [ ] Run focused worker/worktree tests; confirm pass.
- [ ] Commit worker/tests.

## Task 5: Create modal and tool parity

- [ ] Write failing static/API tests for space selector population, selected `space_id` payload, and tool-created task serialization.
- [ ] Add selector using `/api/workspaces`; keep workspace kind control; hide manual path unless needed for compatibility.
- [ ] Add i18n labels through existing locale fallback.
- [ ] Update `tools/kanban_tools.py` payload/detail parity.
- [ ] Run static UI/API tests and relevant Kanban tool tests.
- [ ] Commit UI/tool/tests.

## Task 6: Full verification and live read-back

- [ ] Run focused WebUI tests via `./scripts/test.sh`.
- [ ] Run focused Hermes Agent Kanban tests with repository-supported test runner.
- [ ] Run neighboring workspace, remote-terminal, Kanban DB, worker terminal, and worktree suites.
- [ ] Verify git diff contains no unrelated changes; preserve pre-existing modifications.
- [ ] Read back registered space and a created task in an isolated state fixture; assert stable ID, SSH alias, remote path, and no scratch downgrade.
- [ ] Report any live Mac SSH verification that cannot safely run from VPS as an explicit unverified boundary.

## Verification commands

- WebUI: `./scripts/test.sh tests/test_remote_terminal_workspace.py tests/test_issue3797_kanban_cli_parity.py` plus the named new WebUI regression test file after it is created.
- Hermes Agent: use its repository test runner for the named new Kanban DB/worker regression test files after they are created, plus `tests/hermes_cli/test_kanban_db.py`, `tests/hermes_cli/test_kanban_worker_terminal_cwd.py`, and `tests/hermes_cli/test_kanban_worktree_isolation.py`.
- Source integrity: `git diff --check` and `git status --short` in both repositories.

## Explicit boundaries

- Existing uncommitted WebUI files (`api/agent_health.py`, `api/profiles.py`, `api/routes.py`, `static/panels.js`, `tests/test_profile_status.py`) are not to be reverted or bundled.
- No `rm -rf`.
- No credentials/private keys in JSON or task DB.
- No success claim without fresh test output and read-back evidence.

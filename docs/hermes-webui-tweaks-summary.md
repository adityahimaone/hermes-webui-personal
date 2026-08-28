# Hermes WebUI Personal Tweaks — Migration Summary

> Comprehensive handoff for migrating personal Hermes WebUI changes to [Hermes Studio](https://github.com/EKKOLearnAI/hermes-studio).
>
> Source repository: `nesquena/hermes-webui`
> Personal branch: `personal`
> Baseline in this checkout: `origin/master` at `e168b67e` (`exp-v0.52.264`)
> Current personal tip: `a9f8f90e`
>
> This document describes the delta owned by this fork. It is not a full Hermes WebUI product specification.

## 1. Executive summary

Personal changes fall into five groups:

1. **Kanban approval gates** for preflight, review, and push lifecycle states.
2. **Kanban task controls** for stopping, pausing, resuming, and safely reclaiming workers.
3. **Persistent workspace spaces** with stable IDs and local/SSH transport metadata.
4. **Remote workspace support** for Mac/Windows paths, SSH execution context, workspace health, filemap, and checkpoint behavior.
5. **Personal operator surfaces**: Evonic-style knowledge/profile reads, searchable workspace comboboxes, status indicators, richer task detail, and delegated-context isolation.

The core migration value is not the visual layer. It is the workspace/transport contract:

```text
selected space
  -> stable space_id
  -> canonical transport + target path
  -> persisted task snapshot
  -> worker terminal environment
  -> same target for task execution
```

Without this chain, a remote path can be misread as a VPS-local path or silently downgraded to `scratch`.

## 2. Change inventory

### Personal commits

| Commit | Change |
|---|---|
| `25da5374` | Added personal fork header and upstream sync instructions to root README. |
| `27e160d0` | Initial personal bundle: Kanban gates, remote SSH/workspace fallback, Evonic integration, combobox, UI tweaks, delegated-context cleanup. |
| `c1f28d92` | Added Evonic personal-tweak archive/inventory. |
| `aa5a908a` | Added persistent remote Kanban spaces design specification. |
| `c8ccd159` | Added persistent remote Kanban spaces implementation plan. |
| `2f783cb5` | Persisted remote spaces and added task-space plumbing/tests. |
| `7bf39395` | Made task spaces primary in the Kanban UI and updated CLI-parity test expectation. |
| `3d9024e5` | Preserved compatibility with older `create_task` signatures. |
| `6e4cffaf` | Replaced browser prompts with system confirm/prompt dialogs for destructive Kanban actions. |
| `b5e209b0` | Added preflight/review/push approval gate UI in task detail. |
| `a9f8f90e` | Propagated SSH transport context into Kanban agent thread environment. |

### Files changed by personal delta

| Area | Files |
|---|---|
| Workspace registry and health | `api/workspace.py` |
| Kanban task bridge/actions | `api/kanban_bridge.py` |
| Checkpoint behavior | `api/rollback.py` |
| HTTP routes and Evonic-compatible reads | `api/routes.py` |
| Agent thread environment | `api/streaming.py` |
| Server process isolation | `server.py` |
| Kanban UI and task detail | `static/panels.js` |
| Kanban modal markup | `static/index.html` |
| Styling/status indicators | `static/style.css` |
| Locale additions | `static/i18n.js` |
| Searchable selector | `static/shadcn-combobox.js` |
| Regression coverage | `tests/test_issue3797_kanban_cli_parity.py`, `tests/test_kanban_remote_thread_env.py`, `tests/test_persistent_remote_spaces.py` |
| Documentation | `docs/evonic-personal-tweaks.md`, `docs/superpowers/specs/2026-08-28-persistent-remote-spaces-design.md`, `docs/superpowers/plans/2026-08-28-persistent-remote-spaces.md` |

## 3. Kanban approval gates

### Product behavior

Task detail reads the latest blocked event. When block reason has one of these prefixes, it renders an actionable gate:

| Block reason | UI | Action |
|---|---|---|
| `preflight-approval:` | `Preflight failed — approve to continue` | `Approve preflight` |
| `review-required:` | `Work done — review and approve` | `Commit` or `Request fix` |
| `push-approval:` | `Ready to push` | `Push` |

Gate action sequence:

1. POST a task comment describing operator action.
2. PATCH task status to `ready`.
3. Reload task detail.
4. Refresh Kanban board.

`Request fix` opens a system prompt dialog. Submitted notes become a task comment prefixed with `fix:`.

### Why this exists

Worker lifecycle requires explicit human checkpoints before:

- approving a preflight failure,
- committing reviewed changes,
- pushing changes to a remote repository.

This keeps approval visible inside task detail instead of requiring CLI intervention.

### Hermes Studio migration

Port as a Kanban/task-detail capability, not as a generic modal rewrite. Find Studio's equivalent for:

- task status event history,
- task comments,
- status transition API,
- confirmation/prompt dialog,
- task detail refresh/cache invalidation.

Preserve gate reason prefixes or replace them with typed event fields. Typed fields preferable. Do not depend on parsing display text long-term.

## 4. Kanban worker controls

### Card actions

| Current task status | Controls |
|---|---|
| `running` | `Stop`, `Pause` |
| `blocked` | `Resume`, `Archive` |
| Other active states | Existing `Complete`, `Archive` behavior |

### Backend endpoints

```text
POST /api/kanban/tasks/{task_id}/reclaim
POST /api/kanban/tasks/{task_id}/pause
```

Payload:

```json
{"reason": "stopped from card"}
```

`reclaim`:

- validates task ID,
- calls Kanban `reclaim_task`,
- fails if task is missing or not reclaimable,
- returns refreshed task data.

`pause`:

- reclaims worker first when status is `running`,
- blocks task afterward,
- returns refreshed task data.

Frontend always asks for confirmation before destructive action. No native browser `confirm()`/`prompt()` remains in these flows.

### Hermes Studio migration

Map to Studio's task worker control plane. Preserve lifecycle semantics:

```text
Stop  = terminate worker + return task to queue
Pause = terminate worker + move task to blocked
Resume = blocked -> ready
```

Verify race behavior for a worker finishing while Stop/Pause request is in flight. Backend remains source of truth.

## 5. Persistent workspace spaces

### Problem fixed

Previously, spaces behaved mostly as display-name/path entries. A remote path such as `/Users/...` could be treated as a local path on the VPS and Kanban task creation could lose its execution target by falling back to `scratch`.

### Registry

Workspace records are stored in:

```text
$HERMES_HOME/webui/workspaces.json
```

Normalized records include:

```json
{
  "id": "remote-mac-saas",
  "name": "Remote MAC SAAS",
  "path": "/Users/adityahimawan/Development/saas",
  "transport": "ssh",
  "ssh_target": "mac-tailscale",
  "remote_path": "/Users/adityahimawan/Development/saas"
}
```

Rules:

- Existing `{path, name}` records remain readable.
- Missing IDs are generated from normalized names, with a hash fallback.
- Legacy records default to `transport: local`.
- Names are display values, not identifiers.
- Remote-looking named entries are normalized to SSH records.
- Mac defaults to `mac-tailscale`.
- Windows defaults to `windows-tailscale`.
- SSH credentials and private keys are never stored in WebUI state.
- Normalized data is persisted on next read/write.

### Task creation contract

Kanban create modal now submits `space_id` when a space is selected:

```json
{
  "workspace_kind": "worktree",
  "space_id": "remote-mac-saas"
}
```

The selected space is authoritative. Bridge resolution chooses:

| Transport | Canonical path |
|---|---|
| `local` | `space.path` |
| `ssh` | `space.remote_path` |

`workspace_kind` remains:

- `scratch`
- `worktree`
- `dir`

Unknown `space_id`, unsupported transport, or missing canonical path fails with a validation error. No silent local/scratch fallback.

### Compatibility behavior

The bridge inspects the runtime `create_task` signature. Unsupported optional fields are removed before invocation, preserving compatibility with older Kanban runtime signatures.

Existing tasks without space metadata continue through legacy behavior. Arbitrary path prefixes are not enough for migration; only registered spaces are authoritative.

### Hermes Studio migration

Implement this as a durable project/workspace model:

1. Add stable space/project ID.
2. Store transport type separately from display path.
3. Add optional SSH target alias and target-side path.
4. Send ID, not only user-visible path, from UI.
5. Resolve ID server-side.
6. Persist an immutable task execution snapshot.
7. Keep credentials in SSH config/secrets manager, never task JSON or DB.

Do not migrate only the combobox. The worker routing and task persistence are the important parts.

## 6. Remote workspace support

### Trusted path handling

Registered workspaces are checked before local filesystem existence checks. This allows a known remote path to remain trusted on a host where the path cannot be `stat()`-ed.

This fixes the failure mode where a Mac workspace is shown as inactive because the WebUI server runs on Linux.

### Checkpoints

`api/rollback.py` now distinguishes remote workspaces:

- Listing checkpoints for a known remote workspace returns an empty, explicit remote response instead of a hard local-path error.
- Diffing a remote checkpoint returns a clear error explaining that checkpoints live on the remote host.
- Restoring a remote checkpoint is rejected with an explicit remote-host message.

This is intentionally fail-closed. The VPS must not pretend to restore a checkpoint it cannot access.

### Workspace health

New helpers classify workspace paths as:

```text
local
remote-mac
remote-win
unknown
```

Remote health uses Tailscale `ping` first and ICMP `ping` fallback. Results are:

- cached for 30 seconds,
- batched across workspaces,
- pinged in parallel for distinct remote hosts,
- exposed through:

```text
GET /api/workspaces/health
GET /api/workspaces/health?path=<encoded-path>
GET /api/workspaces/health?force=1
```

UI indicators show local/remote/reachable/offline/unknown state and reduce visual emphasis for offline rows.

### Filemap

Local workspace filemap read endpoint:

```text
GET /api/workspaces/filemap?path=<encoded-path>
```

Behavior:

- reads `<workspace>/artifacts/filemap.json`,
- returns `null` when absent with a generation hint,
- rejects blocked or missing workspaces,
- caps file size at 2 MB,
- validates top-level JSON shape contains `files`,
- does not serve remote-host filemaps from the VPS.

### Remote thread environment

When active workspace matches a registered SSH space, agent thread environment receives:

```text
TERMINAL_ENV=ssh
TERMINAL_SSH_HOST=<configured SSH alias>
TERMINAL_CWD=<remote target path>
```

Current implementation resolves SSH by matching registered SSH `remote_path` to the active workspace path. A future migration should prefer task snapshot ID over path matching, because IDs avoid ambiguity when two spaces share paths.

## 7. Evonic-inspired personal surfaces

These additions were designed to preserve useful Evonic workflows inside WebUI without importing Evonic itself.

### Profile-scoped skills

```text
GET /api/skills?profile=<name>
```

If the profile has a skills directory, response reads that profile's skills. Otherwise it falls back to active profile behavior.

### Profile-scoped memory

```text
GET /api/memory?profile=<name>
```

Reads the selected profile's memory directory when the profile exists. Invalid/missing profile falls back to active profile.

### Knowledge base

```text
GET /api/knowledge?profile=<name>&view=list
GET /api/knowledge?profile=<name>&view=graph
```

List response exposes knowledge documents. Graph response exposes:

- document nodes,
- links between known documents,
- dangling links,
- count,
- KB path.

The implementation reads Evomem SQLite metadata when present and falls back to Markdown files in `kb/`. Default-profile lookup can fall back to `jihyo`, `karina`, or `ningning` when their KB exists.

### Migration guidance

Port these as optional profile/knowledge modules. Keep profile state boundaries explicit. Do not hardcode personal profile names in product logic; use configuration or user-owned profile discovery.

## 8. UI/UX changes

### Kanban modal

- Workspace selection changed from free-form-first to registered **Space** selection.
- Manual workspace path moved under an advanced disclosure.
- Workspace kind label changed to **Execution mode**.
- Selected space submits `space_id` and suppresses duplicate manual path submission.
- Searchable shadcn-style combobox added for workspace paths.
- Existing task paths and registered WebUI workspaces populate selector options.

### Kanban board

- Column headers use status-specific color tints.
- Status dots added before column labels.
- Header corners rounded consistently.
- Board accent follows selected board color.
- Counts for `ready`, `blocked`, and `running` receive stronger semantic emphasis.
- Reduced-motion preference disables workspace remote-dot animation.

### Task detail

- Worker log moved into a full-width section.
- Log has copy action, size/truncation metadata, max-height, and responsive sizing.
- Lightweight log colorization distinguishes reasoning, Hermes output, commands, errors, warnings, success, and info.
- Comments moved into a full-width section below the worker log.
- Buttons receive consistent border, hover, disabled, secondary, and primary states.
- Task ID copy action added.
- Approval gate actions appear in task detail.

### Personal visual direction

The fork follows the existing calm-console direction rather than adding a new framework:

- Python standard-library backend,
- vanilla JavaScript frontend,
- no bundler,
- no frontend framework,
- restrained surfaces and semantic status colors,
- progressive disclosure for advanced workspace input.

## 9. Server isolation fix

`server.py` clears delegated-child environment/context at import time:

```text
HERMES_DELEGATED_CHILD_CONTEXT
HERMES_KANBAN_BOARD
HERMES_KANBAN_TASK
HERMES_KANBAN_RUN_ID
```

It also resets the in-process delegated context flag when available.

Reason: WebUI launched from a delegated child could inherit Kanban context and intermittently hit DB locking/migration behavior. WebUI server startup must behave as an independent process, not as a Kanban child worker.

### Hermes Studio migration

Studio likely has a separate Node process boundary. Preserve the invariant instead of copying environment-variable names:

- Web dashboard process has no worker task identity by default.
- Worker context is created explicitly per task.
- Request-scoped/task-scoped context cannot leak into global server state.

## 10. Tests added or updated

Personal regression coverage includes:

- persistent remote space normalization,
- stable space IDs,
- local vs SSH transport metadata,
- task creation with selected space,
- no remote-path downgrade,
- task-space persistence compatibility,
- remote Kanban thread environment,
- Kanban CLI parity expectation updates.

Repository-required test runner:

```bash
./scripts/test.sh
```

Focused examples:

```bash
./scripts/test.sh tests/test_persistent_remote_spaces.py -v
./scripts/test.sh tests/test_kanban_remote_thread_env.py -v
./scripts/test.sh tests/test_issue3797_kanban_cli_parity.py -v
```

Static integrity check:

```bash
git diff --check origin/master..HEAD
```

Verification observed for this snapshot:

```text
diff-check=passed
```

The checkout also contains unrelated pre-existing uncommitted changes:

```text
M api/agent_health.py
M api/profiles.py
M api/routes.py
M uv.lock
?? tests/test_profile_status.py
```

Do not bundle or revert those files during migration review without separate scope confirmation.

## 11. Known limitations and migration risks

### 11.1 WebUI is tightly coupled to Hermes Agent internals

Current WebUI imports Agent modules and reads Agent state layout directly. Hermes Studio has a larger Node/Vue/Koa architecture and keeps Studio state separate from Hermes Agent state. Do not port imports mechanically.

Recommended boundary:

```text
Studio API/service
  -> Hermes adapter/client
  -> explicit task/session/workspace contract
```

### 11.2 Remote detection currently uses path/name conventions

Current normalization recognizes remote entries through SSH transport or names beginning with `Remote `. Path-prefix classification also recognizes `/Users/`, `/c/`, `/d/`, `/C:`, and `/D:` patterns.

Studio migration should replace convention-based inference with explicit transport configuration. Unknown transport must remain blocked/unknown, not local.

### 11.3 Workspace health host mapping is deployment-specific

The current implementation maps known path prefixes to Tailscale addresses. This is useful for the personal VPS setup but should not be copied as product defaults. Studio should store a configured health target or call a target-aware SSH preflight.

### 11.4 Filemap and checkpoint data are host-local

Remote workspace UI can show metadata, but VPS-local filemap/checkpoint endpoints cannot prove remote state. Studio needs target-side APIs or explicit unavailable states.

### 11.5 Gate actions currently encode comments as control signals

Comments preserve auditability, but typed control events are cleaner. During migration, maintain compatibility with existing task history before changing event schema.

### 11.6 No full end-to-end Mac SSH proof in this repository snapshot

The code and focused regression tests cover metadata propagation and environment construction. A real remote execution test must run against configured SSH/Tailscale target and should be treated as a separate acceptance check.

### 11.7 No direct memory/state migration assumed

Do not copy personal `~/.hermes` state wholesale into Studio. Separate:

- Hermes Agent profiles/config/memory/skills,
- Studio sessions/settings/cache,
- workspace registry,
- Kanban task database,
- SSH credentials/config.

## 12. Porting checklist to Hermes Studio

### Phase A — inventory and boundary

- [ ] Pin source WebUI commit range: `origin/master..a9f8f90e`.
- [ ] Identify Studio equivalents for sessions, Kanban/tasks, profiles, workspaces, comments, events, and workers.
- [ ] Read Studio module-boundary documentation before editing.
- [ ] Decide whether Kanban remains in Studio or stays in Hermes Agent adapter.
- [ ] Keep Studio state separate from Hermes Agent state.

### Phase B — workspace contract

- [ ] Add stable workspace/space IDs.
- [ ] Add explicit `transport: local | ssh`.
- [ ] Add target-side path separate from display/local path.
- [ ] Reference SSH aliases, never private key contents.
- [ ] Validate configured aliases server-side.
- [ ] Reject unknown IDs and unsupported transport.
- [ ] Persist immutable task execution snapshot.
- [ ] Add local/remote/unknown health states.
- [ ] Show explicit unavailable state for remote filemap/checkpoint data.

### Phase C — Kanban lifecycle

- [ ] Port preflight approval gate.
- [ ] Port review -> commit/request-fix gate.
- [ ] Port push approval gate.
- [ ] Port Stop/Pause/Resume controls.
- [ ] Preserve backend race safety and audit comments/events.
- [ ] Use typed events if Studio task schema supports them.

### Phase D — UI

- [ ] Port Space selector before manual path input.
- [ ] Keep manual path as advanced compatibility path.
- [ ] Port status dots and offline indicators.
- [ ] Port full-width worker log and comments.
- [ ] Port log copy and semantic colorization only if Studio design system supports it.
- [ ] Recreate responsive behavior in Vue/Naive UI, not by copying vanilla CSS wholesale.

### Phase E — profile/knowledge features

- [ ] Decide whether profile-scoped skills are needed in Studio.
- [ ] Decide whether profile-scoped memory is needed.
- [ ] Port knowledge list/graph only if Evomem integration remains in scope.
- [ ] Remove hardcoded personal profile fallback names.
- [ ] Add auth and profile-boundary tests.

### Phase F — verification

- [ ] Unit test legacy workspace normalization.
- [ ] Unit test local and SSH task snapshots.
- [ ] Test unknown space rejection.
- [ ] Test SSH preflight failure does not fall back local.
- [ ] Test Stop/Pause race with worker completion.
- [ ] Test gate transitions and audit trail.
- [ ] Test profile isolation.
- [ ] Test remote unavailable UI state.
- [ ] Run Studio lint/typecheck/unit/build commands.
- [ ] Run real SSH acceptance test against a safe non-production workspace.
- [ ] Compare memory/RAM footprint before and after migration.

## 13. What not to port blindly

- Personal Tailscale IP mappings.
- Personal SSH aliases as product defaults.
- Evonic profile names (`jihyo`, `karina`, `ningning`) as hardcoded behavior.
- Vanilla JS DOM functions.
- WebUI route handlers copied into Koa controllers without service boundaries.
- Hermes WebUI `workspaces.json` as Studio's only source of truth.
- Comments/event reason parsing as the final typed contract.
- Full WebUI state directory copied into Studio state.
- Root README product claims that describe upstream functionality rather than this personal delta.

## 14. Recommended migration order

1. Port workspace/transport model.
2. Port task snapshot persistence.
3. Port worker routing and fail-closed SSH preflight.
4. Port Stop/Pause/Resume controls.
5. Port approval gates.
6. Port workspace health and explicit remote-unavailable states.
7. Port task-detail presentation.
8. Port optional profile/knowledge surfaces.
9. Measure RAM and remove duplicated WebUI runtime layers.

Workspace transport first. UI polish later. Otherwise Studio can look correct while tasks still execute on wrong host.

## 15. Source references

- `docs/superpowers/specs/2026-08-28-persistent-remote-spaces-design.md`
- `docs/superpowers/plans/2026-08-28-persistent-remote-spaces.md`
- `docs/evonic-personal-tweaks.md`
- `AGENTS.md`
- `CONTRIBUTING.md`
- `docs/CONTRACTS.md`
- `DESIGN.md`
- `https://github.com/EKKOLearnAI/hermes-studio`

---

Status: migration handoff document. No runtime behavior changed by this file.

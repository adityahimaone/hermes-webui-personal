# Persistent Remote Spaces for Kanban Tasks

## Problem

WebUI spaces currently act as a display-name/path list. Kanban task creation accepts `workspace_kind` and `workspace_path`, but the bridge downgrades remote-looking paths such as `/Users/...` to `scratch`. The worker therefore loses the selected project location and may execute on the VPS instead of the Mac.

Card `t_5dd6c5f3` reproduces the failure shape: a task selected for the SAAS project needs remote Mac execution, but the persisted task workspace is scratch and the worker has no authoritative transport target.

## Goals

- Make spaces durable execution targets, not labels only.
- Let Kanban tasks reference a stable space ID.
- Preserve `worktree` vs `dir` semantics inside the selected space.
- Route `Remote MAC SAAS` through SSH alias `mac-tailscale`.
- Prevent silent remote-to-local/scratch fallback.
- Reuse one canonical target for all tasks using the same space.
- Preserve backward compatibility for existing tasks and plain local workspace entries.

## Non-goals

- No arbitrary SSH credential storage in WebUI state.
- No new dependency or frontend framework.
- No broad Kanban redesign.
- No automatic migration of unrelated personal configuration.

## Canonical space model

`~/.hermes/webui/workspaces.json` remains the durable registry. Entries normalize to:

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

Legacy entries with only `path` and optional `name` normalize as `transport: "local"`, with a stable ID generated once and persisted. Display names are not identifiers. SSH aliases are references to the user's SSH configuration; private keys and credentials never enter the JSON file.

The existing Remote MAC entries must be represented as SSH spaces. Local VPS entries remain local. Windows entries may remain registered but are not silently treated as local until their transport is explicitly known; unsupported transport is an explicit blocked state.

## Task contract

Create-task payload adds `space_id`. The selected space is authoritative for execution target. `workspace_kind` remains `scratch | worktree | dir`:

- `scratch`: task scratch behavior, still scoped by selected space when a space is selected.
- `dir`: use the space's canonical directory.
- `worktree`: create/use worktree from the space's canonical repository.

The bridge resolves and persists the space snapshot needed by the worker:

- stable space ID
- space display name
- transport
- SSH target when remote
- target-side path
- workspace kind

The snapshot prevents later space edits from changing a running task's target. No remote path is converted to `scratch`. Unknown or invalid space references fail closed with a user-visible validation error.

Existing tasks without `space_id` continue through current behavior. Existing tasks whose path exactly matches a registered space may be normalized on read, but migration must not guess from arbitrary path prefixes.

## Execution flow

1. Modal loads registered spaces and shows space selector.
2. User selects `Remote MAC SAAS` and workspace kind.
3. WebUI submits `space_id`, kind, and only compatible path metadata.
4. Bridge validates the stable ID and resolves the canonical target.
5. Kanban persists the resolved snapshot with task.
6. Worker selects execution backend from persisted transport:
   - local → existing local runner
   - SSH → command runner using allowlisted `ssh_target`, with remote cwd
7. Worker prompt/context states the selected space, transport, SSH alias, and remote cwd. It explicitly forbids treating remote path as VPS-local path.
8. SSH preflight failure blocks task with diagnostic; it never retries by executing locally.

For `worktree`, repository discovery and worktree creation happen on the target machine. The remote worktree path is returned and used consistently for later commands. All decisions and actions consume the same resolved snapshot.

## Reuse and artifacts

Space ID is the cache/index key. Filemap/artifact metadata attaches to the space and may be reused by later tasks. Task-specific worktree state remains task-scoped. Cache invalidation occurs when the canonical target or transport changes; task snapshots remain immutable.

## Error handling and security

- Reject empty or unknown `space_id`.
- Validate remote POSIX path and containment under configured `remote_path`.
- Allow only configured SSH aliases; do not interpolate arbitrary user input as a host.
- Store no credentials or private key contents.
- Fail closed on missing transport, SSH preflight failure, invalid target, or target mismatch.
- Preserve diagnostics in task log/status so operator can fix configuration without guessing.

## Compatibility and rollout

- Read legacy workspace entries and normalize them on next write.
- Keep existing task columns/fields readable.
- Add nullable task fields or serialized metadata without destructive migration.
- Keep current scratch tasks operational.
- Ship focused tests before implementation: space normalization, create payload, bridge no-downgrade behavior, task snapshot round-trip, local/SSH routing, SSH failure fail-closed, same-space reuse, and the `t_5dd6c5f3` regression shape.

## Verification

Required evidence:

- New regression tests fail against current code for remote path downgrade / lost target.
- Focused WebUI and Kanban tests pass after implementation.
- Neighboring workspace, Kanban, and remote-terminal tests pass through `./scripts/test.sh`.
- Read-back of persisted space/task data confirms stable ID and SSH target.
- Manual UI check confirms selecting `Remote MAC SAAS` sends its stable ID and does not display or submit a silent scratch fallback.

## Contract routing

- `AGENTS.md`
- `CONTRIBUTING.md`
- `docs/CONTRACTS.md`
- `docs/GUIDELINES.md`
- `docs/rfcs/README.md` for runtime/state contract review

## Open implementation boundary

The exact Kanban runtime module and persistence adapter will be selected during implementation after inspecting the current Hermes Agent Kanban source. The behavior above is fixed; module names are intentionally not guessed in this design stage.

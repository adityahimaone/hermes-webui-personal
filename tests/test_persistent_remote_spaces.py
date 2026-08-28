"""Regression tests for durable space-to-task execution metadata."""

from types import SimpleNamespace

import api.kanban_bridge as bridge
import api.workspace as workspace


REMOTE_SPACE = {
    "id": "remote-mac-saas",
    "name": "Remote MAC SAAS",
    "path": "/Users/adityahimawan/Development/saas",
    "transport": "ssh",
    "ssh_target": "mac-tailscale",
    "remote_path": "/Users/adityahimawan/Development/saas",
}


def test_clean_workspace_list_preserves_space_execution_metadata(monkeypatch):
    monkeypatch.setattr(workspace, "_home_path", lambda: workspace.Path("/tmp"))

    cleaned = workspace._clean_workspace_list([REMOTE_SPACE])

    assert cleaned[0]["id"] == "remote-mac-saas"
    assert cleaned[0]["transport"] == "ssh"
    assert cleaned[0]["ssh_target"] == "mac-tailscale"
    assert cleaned[0]["remote_path"] == REMOTE_SPACE["remote_path"]
    assert cleaned[0]["path"] == REMOTE_SPACE["path"]


def test_create_task_payload_keeps_remote_space_target(monkeypatch):
    captured = {}

    monkeypatch.setattr(bridge, "load_workspaces", lambda: [REMOTE_SPACE])
    monkeypatch.setattr(bridge, "_conn", lambda board=None: _Connection())
    monkeypatch.setattr(
        bridge,
        "_kb",
        lambda: SimpleNamespace(
            create_task=lambda conn, **kwargs: (captured.setdefault("task", kwargs), "t_test")[1],
            get_task=lambda conn, task_id: SimpleNamespace(
                id=task_id,
                title="Update Validasi Kuota Early Renewal Gadjian CS",
                workspace_kind=captured["task"]["workspace_kind"],
                workspace_path=captured["task"]["workspace_path"],
                workspace_space_id=captured["task"]["workspace_space_id"],
                workspace_transport=captured["task"]["workspace_transport"],
                workspace_ssh_target=captured["task"]["workspace_ssh_target"],
            ),
        ),
    )

    result = bridge._create_task_payload(
        {
            "title": "Update Validasi Kuota Early Renewal Gadjian CS",
            "space_id": "remote-mac-saas",
            "workspace_kind": "dir",
            "workspace_path": REMOTE_SPACE["path"],
        }
    )

    task = result["task"]
    assert task["workspace_space_id"] == "remote-mac-saas"
    assert task["workspace_transport"] == "ssh"
    assert task["workspace_ssh_target"] == "mac-tailscale"
    assert task["workspace_path"] == REMOTE_SPACE["remote_path"]
    assert task["workspace_kind"] == "dir"


class _Connection:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, *args):
        return self

    def fetchone(self):
        return None

    def fetchall(self):
        return []


class _Unused:
    pass

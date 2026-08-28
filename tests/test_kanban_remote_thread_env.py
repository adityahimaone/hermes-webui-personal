from api import streaming


def test_remote_space_overrides_worker_terminal_transport(monkeypatch):
    monkeypatch.setattr("api.workspace.load_workspaces", lambda: [{
        "transport": "ssh",
        "remote_path": "/Users/adityahimawan/Development/saas",
        "ssh_target": "mac-tailscale",
    }])
    env = streaming._build_agent_thread_env(
        {"TERMINAL_ENV": "local", "TERMINAL_CWD": "/home/adityahimaone/workspace"},
        "/Users/adityahimawan/Development/saas", "session", "/tmp/profile",
    )
    assert env["TERMINAL_ENV"] == "ssh"
    assert env["TERMINAL_SSH_HOST"] == "mac-tailscale"
    assert env["TERMINAL_CWD"] == "/Users/adityahimawan/Development/saas"

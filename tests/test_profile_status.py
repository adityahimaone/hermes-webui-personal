from pathlib import Path
import sqlite3

def test_profile_status_chat_uses_recent_activity(tmp_path):
    from api import profiles
    home = tmp_path / "default"
    home.mkdir()
    db = home / "state.db"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE sessions (id TEXT PRIMARY KEY, source TEXT, profile_name TEXT, title TEXT, started_at REAL, ended_at REAL, last_activity_at REAL)")
    conn.execute("INSERT INTO sessions VALUES ('s1','webui','default','Live chat',100.0,NULL,1000.0)")
    conn.commit(); conn.close()
    status = profiles._profile_status('default', home, now=1000.0, kanban_tasks=[])
    assert status['status'] == 'busy'
    assert status['source'] == 'chat'
    assert status['title'] == 'Live chat'

def test_profile_status_done_kanban_is_not_running(tmp_path):
    from api import profiles
    status = profiles._profile_status('default', tmp_path, now=1000.0, kanban_tasks=[{'status':'done','title':'Finished','assignee':'default'}])
    assert status['status'] != 'running'

if __name__ == '__main__':
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        test_profile_status_chat_uses_recent_activity(Path(d))
        test_profile_status_done_kanban_is_not_running(Path(d))
    print('profile status self-check: PASS')

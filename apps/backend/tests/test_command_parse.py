from fastapi.testclient import TestClient

from app.main import create_app


def test_parse_creates_plan() -> None:
    client = TestClient(create_app())

    # create a project
    pr = client.post(
        "/projects",
        json={"name": "demo", "repo_path": "C:/tmp/demo"},
    )
    assert pr.status_code == 200
    project_id = pr.json()["id"]

    resp = client.post(
        "/commands/parse",
        json={"project_id": project_id, "text": "Deploy v1.6 to staging and run tests"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "pending_approval"
    assert body["action"] in {"deploy", "unknown"}
    assert "staging" in body["environments"]

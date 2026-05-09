from fastapi.testclient import TestClient

from backend.app import app


class StubRunner:
    def run_action(self, action: str, files: list[str], pairs: list[dict]) -> dict:
        if action == "preview":
            return {
                "status": "complete",
                "matches": [
                    {
                        "file": files[0],
                        "entity_type": "DBText",
                        "layer": "0",
                        "current_value": "OLD",
                        "proposed_value": "NEW",
                        "space": "Model",
                    }
                ],
                "files_scanned": 1,
                "total_matches": 1,
                "errors": [],
            }
        return {
            "status": "complete",
            "total_changes": 1,
            "files_modified": 1,
            "errors": [],
        }


def test_health(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_preview_valid_input(client: TestClient, monkeypatch) -> None:
    app.state.runner = StubRunner()
    response = client.post(
        "/api/preview",
        json={
            "files": ["C:/tmp/test.dwg"],
            "pairs": [
                {
                    "find": "OLD",
                    "replace": "NEW",
                    "case_sensitive": False,
                    "use_regex": False,
                }
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_matches"] == 1


def test_preview_invalid_input(client: TestClient) -> None:
    response = client.post("/api/preview", json={"files": [], "pairs": []})
    assert response.status_code == 400

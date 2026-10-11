"""
API endpoint integration tests using Starlette TestClient.
"""
from starlette.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "Compiler Service"


def test_examples_endpoint():
    response = client.get("/api/examples")
    assert response.status_code == 200
    examples = response.json()
    assert len(examples) >= 4
    ids = [e["id"] for e in examples]
    assert "sample_1" in ids
    assert "sample_syntax_err" in ids
    assert "sample_semantic_err" in ids


def test_api_compile_valid_code():
    code = """int main() {
    int arr[4] = {10, 20, 30, 40};
    int sum = 0;
    for (int i = 0; i < 4; i++) {
        sum += arr[i];
    }
    return 0;
}"""
    response = client.post("/api/compile", json={"source_code": code})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["stages"]["lexical"]["status"] == "success"
    assert data["stages"]["syntax"]["status"] == "success"
    assert data["stages"]["semantic"]["status"] == "success"
    assert data["stages"]["ir"]["status"] == "success"
    assert data["stages"]["pim_mapping"]["status"] == "success"
    assert len(data["tokens"]) > 0
    assert data["ast"] is not None
    assert len(data["ir"]["instructions"]) > 0
    assert data["mapping"]["pim_count"] > 0
    assert data["mapping"]["cpu_count"] > 0


def test_api_compile_syntax_error():
    code = "int x = 10\nint y = 20;"
    response = client.post("/api/compile", json={"source_code": code})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["stages"]["syntax"]["status"] == "error"
    assert len(data["diagnostics"]) > 0


def test_api_compile_semantic_error():
    code = "int x = 10; z = x + 5;"
    response = client.post("/api/compile", json={"source_code": code})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["stages"]["semantic"]["status"] == "error"
    assert any("Undeclared variable 'z'" in d["message"] for d in data["diagnostics"])


def test_api_compile_empty_code():
    response = client.post("/api/compile", json={"source_code": ""})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["stages"]["lexical"]["status"] == "error"

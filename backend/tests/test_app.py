from fastapi.testclient import TestClient

from app.core.errors import AppError
from app.main import app, create_app


def test_root_route_is_preserved() -> None:
    response = TestClient(app).get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}
    assert response.headers.get("X-Request-ID")


def test_health_check_returns_ok() -> None:
    response = TestClient(app).get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "smartcampus-backend"
    assert body["timestamp"]


def test_caller_request_id_is_returned() -> None:
    request_id = "client-request-123"
    response = TestClient(app).get("/api/v1/health", headers={"X-Request-ID": request_id})

    assert response.headers["X-Request-ID"] == request_id


def test_unknown_route_uses_common_error_shape() -> None:
    response = TestClient(app).get("/route-does-not-exist")

    assert response.status_code == 404
    body = response.json()
    assert set(body) == {"error"}
    assert body["error"]["code"] == "NOT_FOUND"
    assert body["error"]["message"]
    assert body["error"]["request_id"] == response.headers["X-Request-ID"]
    assert body["error"]["details"] == []


def test_app_errors_use_common_error_shape() -> None:
    test_app = create_app()

    @test_app.get("/test-error")
    async def raise_app_error() -> None:
        raise AppError(code="EXAMPLE_ERROR", message="Example failure", status_code=409)

    response = TestClient(test_app).get("/test-error")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EXAMPLE_ERROR"
    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]


def test_validation_errors_use_common_error_shape() -> None:
    test_app = create_app()

    @test_app.get("/test-validation")
    async def needs_integer(value: int) -> dict[str, int]:
        return {"value": value}

    response = TestClient(test_app).get("/test-validation", params={"value": "invalid"})

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert error["details"]
    assert error["request_id"] == response.headers["X-Request-ID"]


def test_unexpected_errors_use_common_error_shape() -> None:
    test_app = create_app()

    @test_app.get("/test-unexpected-error")
    async def raise_unexpected_error() -> None:
        raise RuntimeError("internal detail")

    response = TestClient(test_app, raise_server_exceptions=False).get(
        "/test-unexpected-error"
    )

    assert response.status_code == 500
    error = response.json()["error"]
    assert error["code"] == "INTERNAL_SERVER_ERROR"
    assert error["message"] == "An internal error occurred."
    assert error["request_id"] == response.headers["X-Request-ID"]


def test_openapi_and_documentation_routes_are_available() -> None:
    client = TestClient(app)
    schema_response = client.get("/openapi.json")

    assert schema_response.status_code == 200
    schema = schema_response.json()
    assert schema["info"]["title"] == "SmartCampus API"
    assert "/api/v1/health" in schema["paths"]
    health_responses = schema["paths"]["/api/v1/health"]["get"]["responses"]
    assert health_responses["400"]["content"]["application/json"]["schema"]["$ref"] == (
        "#/components/schemas/ErrorResponse"
    )
    assert health_responses["500"]["content"]["application/json"]["schema"]["$ref"] == (
        "#/components/schemas/ErrorResponse"
    )
    assert "ErrorResponse" in schema["components"]["schemas"]
    assert client.get("/docs").status_code == 200
    assert client.get("/redoc").status_code == 200

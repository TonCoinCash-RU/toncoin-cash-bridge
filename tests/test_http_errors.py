from app.http_errors import internal_error_http, provider_error_http, value_error_http


def test_value_error_http_uses_code_as_message():
    exc = value_error_http(ValueError("bridge_amount_too_small"))
    assert exc.status_code == 400
    assert exc.detail == {
        "code": "bridge_amount_too_small",
        "message": "bridge_amount_too_small",
    }


def test_provider_error_http_hides_internals():
    exc = provider_error_http()
    assert exc.status_code == 502
    assert exc.detail == {"code": "provider_error", "message": "provider_error"}


def test_internal_error_http_is_generic():
    exc = internal_error_http()
    assert exc.status_code == 500
    assert exc.detail == {"code": "internal_error", "message": "internal_error"}

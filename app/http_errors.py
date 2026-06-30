from fastapi import HTTPException


def value_error_http(exc: ValueError) -> HTTPException:
    code = str(exc)
    return HTTPException(status_code=400, detail={"code": code, "message": code})


def provider_error_http() -> HTTPException:
    return HTTPException(
        status_code=502,
        detail={"code": "provider_error", "message": "provider_error"},
    )


def internal_error_http() -> HTTPException:
    return HTTPException(
        status_code=500,
        detail={"code": "internal_error", "message": "internal_error"},
    )

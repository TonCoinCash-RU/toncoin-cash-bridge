import logging

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .auth import require_api_key
from .bridge_service import bridge_service
from .config import settings
from .http_errors import internal_error_http, provider_error_http, value_error_http
from .schemas import (
    AssetsResponse,
    BuildStepRequest,
    BuildStepResponse,
    HealthResponse,
    QuoteRequest,
    QuoteResponse,
    RouteRequest,
    RouteResponse,
)

log = logging.getLogger("bridge_service")


def _configure_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.app_log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


_configure_logging()
app = FastAPI(title=settings.app_name, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_errors(_: Request, exc: Exception):
    log.exception("unhandled_error")
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    http_exc = internal_error_http()
    return JSONResponse(status_code=http_exc.status_code, content={"detail": http_exc.detail})


@app.get("/healthz", response_model=HealthResponse)
async def healthz() -> dict:
    return {"ok": True, "service": settings.app_name, "env": settings.app_env}


@app.get(
    "/bridge/assets",
    response_model=AssetsResponse,
    dependencies=[Depends(require_api_key)],
)
async def bridge_assets() -> AssetsResponse:
    return bridge_service.list_assets()


@app.post(
    "/bridge/route",
    response_model=RouteResponse,
    dependencies=[Depends(require_api_key)],
)
async def bridge_route(payload: RouteRequest) -> RouteResponse:
    return bridge_service.route(payload.from_asset, payload.to_asset)


@app.post(
    "/bridge/quote",
    response_model=QuoteResponse,
    dependencies=[Depends(require_api_key)],
)
async def bridge_quote(payload: QuoteRequest) -> QuoteResponse:
    try:
        return await bridge_service.quote(
            from_asset=payload.from_asset,
            to_asset=payload.to_asset,
            amount=payload.amount,
            slippage_bps=payload.slippage_bps,
            wallet_address=payload.wallet_address,
            wallets=payload.wallets,
        )
    except ValueError as exc:
        raise value_error_http(exc) from exc
    except Exception as exc:
        log.exception("bridge_quote_failed")
        raise provider_error_http() from exc


@app.post(
    "/bridge/build_step",
    response_model=BuildStepResponse,
    dependencies=[Depends(require_api_key)],
)
async def bridge_build_step(payload: BuildStepRequest) -> BuildStepResponse:
    try:
        return await bridge_service.build_step(
            from_asset=payload.from_asset,
            to_asset=payload.to_asset,
            amount=payload.amount,
            step_order=payload.step_order,
            slippage_bps=payload.slippage_bps,
            wallets=payload.wallets,
        )
    except ValueError as exc:
        raise value_error_http(exc) from exc
    except Exception as exc:
        log.exception("bridge_build_step_failed")
        raise provider_error_http() from exc

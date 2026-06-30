from __future__ import annotations

import logging
from typing import Any

import httpx

from ..config import settings

logger = logging.getLogger(__name__)

_client: httpx.AsyncClient | None = None


def _http() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=30.0)
    return _client


def _base_url() -> str:
    return settings.swap_api_base.rstrip("/")


def _headers() -> dict[str, str]:
    return {
        "x-api-key": settings.swap_api_key,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


class SwapClient:
    async def route(self, *, from_asset: str, to_asset: str) -> dict[str, Any]:
        response = await _http().post(
            f"{_base_url()}/swap/route",
            headers=_headers(),
            json={"from_asset": from_asset, "to_asset": to_asset},
        )
        response.raise_for_status()
        return response.json()

    async def quote(
        self,
        *,
        from_asset: str,
        to_asset: str,
        amount: str,
        slippage_bps: int,
        wallet_address: str | None,
        wallets: dict[str, Any] | None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "from_asset": from_asset,
            "to_asset": to_asset,
            "amount": amount,
            "slippage_bps": slippage_bps,
        }
        if wallet_address:
            payload["wallet_address"] = wallet_address
        if wallets:
            payload["wallets"] = wallets
        response = await _http().post(
            f"{_base_url()}/swap/quote",
            headers=_headers(),
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    async def build_step(
        self,
        *,
        from_asset: str,
        to_asset: str,
        amount: str,
        step_order: int,
        slippage_bps: int,
        wallets: dict[str, Any],
    ) -> dict[str, Any]:
        response = await _http().post(
            f"{_base_url()}/swap/build_step",
            headers=_headers(),
            json={
                "from_asset": from_asset,
                "to_asset": to_asset,
                "amount": amount,
                "step_order": step_order,
                "slippage_bps": slippage_bps,
                "wallets": wallets,
            },
        )
        response.raise_for_status()
        return response.json()

    async def build(
        self,
        *,
        from_asset: str,
        to_asset: str,
        amount: str,
        slippage_bps: int,
        wallet_address: str,
        wallets: dict[str, Any] | None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "from_asset": from_asset,
            "to_asset": to_asset,
            "amount": amount,
            "slippage_bps": slippage_bps,
            "wallet_address": wallet_address,
        }
        if wallets:
            payload["wallets"] = wallets
        response = await _http().post(
            f"{_base_url()}/swap/build",
            headers=_headers(),
            json=payload,
        )
        response.raise_for_status()
        return response.json()


swap_client = SwapClient()

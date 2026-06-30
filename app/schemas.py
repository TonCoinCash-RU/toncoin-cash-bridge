from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    ok: bool
    service: str
    env: str


class BridgeAssetInfo(BaseModel):
    id: str
    symbol: str
    title: str
    chain: str


class AssetsResponse(BaseModel):
    assets: list[BridgeAssetInfo]


class RouteRequest(BaseModel):
    from_asset: str = Field(min_length=2, max_length=16)
    to_asset: str = Field(min_length=2, max_length=16)


class RouteStep(BaseModel):
    order: int
    action: Literal["swap", "bridge"]
    chain: str | None = None
    provider: str | None = None
    description: str | None = None
    from_asset: str | None = None
    to_asset: str | None = None


class RouteResponse(BaseModel):
    kind: str
    available: bool
    provider: str | None = None
    execution: Literal["multi_step", "unavailable"] = "unavailable"
    hint_key: str | None = None
    steps: list[RouteStep] = Field(default_factory=list)
    step_count: int = 0


class WalletAddresses(BaseModel):
    ton: str | None = Field(default=None, max_length=256)
    evm: str | None = Field(default=None, max_length=256)
    solana: str | None = Field(default=None, max_length=256)
    btc: str | None = Field(default=None, max_length=256)


class QuoteRequest(BaseModel):
    from_asset: str = Field(min_length=2, max_length=16)
    to_asset: str = Field(min_length=2, max_length=16)
    amount: str = Field(min_length=1, max_length=64)
    slippage_bps: int = Field(default=100, ge=1, le=5000)
    wallet_address: str | None = Field(default=None, max_length=256)
    wallets: WalletAddresses | None = None


class QuoteResponse(BaseModel):
    provider: str
    from_asset: str
    to_asset: str
    input_amount: str
    output_amount: str
    output_amount_min: str | None = None
    price_impact_pct: float | None = None
    expires_in_seconds: int = 20
    execution: Literal["multi_step", "unavailable"]
    route_kind: str
    step_count: int


class BuildStepRequest(BaseModel):
    from_asset: str = Field(min_length=2, max_length=16)
    to_asset: str = Field(min_length=2, max_length=16)
    amount: str = Field(min_length=1, max_length=64)
    step_order: int = Field(ge=1, le=10)
    slippage_bps: int = Field(default=100, ge=1, le=5000)
    wallets: WalletAddresses


class BuildStepResponse(BaseModel):
    step_order: int
    action: str
    provider: str
    from_asset: str
    to_asset: str
    input_amount: str
    payload: dict
    total_steps: int
    wait_hint: str | None = None
    order_id: str | None = None

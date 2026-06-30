from __future__ import annotations

import logging
from decimal import Decimal, InvalidOperation

from .adapters.swap_client import swap_client
from .assets import parse_asset
from .planner import PlannedLeg, plan_route
from .schemas import (
    AssetsResponse,
    BridgeAssetInfo,
    BuildStepResponse,
    QuoteResponse,
    RouteResponse,
    RouteStep,
    WalletAddresses,
)

logger = logging.getLogger(__name__)

_ASSETS = [
    BridgeAssetInfo(id="tcc", symbol="TCC", title="TonCoin Cash", chain="ton"),
    BridgeAssetInfo(id="btc", symbol="BTC", title="Bitcoin", chain="btc"),
    BridgeAssetInfo(id="sol", symbol="SOL", title="Solana", chain="solana"),
]


class BridgeService:
    def list_assets(self) -> AssetsResponse:
        return AssetsResponse(assets=_ASSETS)

    def route(self, from_asset: str, to_asset: str) -> RouteResponse:
        try:
            src = parse_asset(from_asset)
            dst = parse_asset(to_asset)
        except ValueError:
            return RouteResponse(
                kind="unavailable",
                available=False,
                hint_key="unsupported_asset",
            )

        if src == dst:
            return RouteResponse(
                kind="same_asset",
                available=False,
                hint_key="same_asset",
            )

        legs = plan_route(from_asset, to_asset)
        if not legs:
            return RouteResponse(
                kind="unavailable",
                available=False,
                hint_key="unavailable",
            )

        steps = [
            RouteStep(
                order=leg.order,
                action=leg.action,  # type: ignore[arg-type]
                chain=leg.chain,
                provider=leg.provider,
                description=leg.description,
                from_asset=leg.from_asset,
                to_asset=leg.to_asset,
            )
            for leg in legs
        ]
        return RouteResponse(
            kind="tcc_extended",
            available=True,
            provider="multi",
            execution="multi_step",
            steps=steps,
            step_count=len(steps),
        )

    async def quote(
        self,
        *,
        from_asset: str,
        to_asset: str,
        amount: str,
        slippage_bps: int,
        wallet_address: str | None,
        wallets: WalletAddresses | None,
    ) -> QuoteResponse:
        self._validate_amount(amount)
        route = self.route(from_asset, to_asset)
        if not route.available:
            raise ValueError("pair_unavailable")

        wallets_dict = wallets.model_dump(exclude_none=True) if wallets else None
        legs = plan_route(from_asset, to_asset)
        current_amount = amount
        last_quote: dict | None = None
        index = 0

        while index < len(legs):
            leg = legs[index]
            swap_from, swap_to, swap_step = self._swap_leg_mapping(
                leg, from_asset, to_asset
            )

            if leg.delegate == "swap_tcc_eth_step1":
                wallet = self._wallet_for_asset("tcc", wallet_address, wallets)
                last_quote = await swap_client.quote(
                    from_asset="tcc",
                    to_asset="eth",
                    amount=current_amount,
                    slippage_bps=slippage_bps,
                    wallet_address=wallet,
                    wallets=wallets_dict,
                )
                current_amount = str(last_quote.get("output_amount") or current_amount)
                index += 2
                continue

            if leg.delegate == "swap_eth_tcc":
                wallet = self._wallet_for_asset("eth", wallet_address, wallets)
                last_quote = await swap_client.quote(
                    from_asset="eth",
                    to_asset="tcc",
                    amount=current_amount,
                    slippage_bps=slippage_bps,
                    wallet_address=wallet,
                    wallets=wallets_dict,
                )
                current_amount = str(last_quote.get("output_amount") or current_amount)
                index += 1
                continue

            if swap_step is not None:
                raise ValueError("quote_requires_swap_aggregate")

            wallet = self._wallet_for_asset(swap_from, wallet_address, wallets)
            last_quote = await swap_client.quote(
                from_asset=swap_from,
                to_asset=swap_to,
                amount=current_amount,
                slippage_bps=slippage_bps,
                wallet_address=wallet,
                wallets=wallets_dict,
            )
            current_amount = str(last_quote.get("output_amount") or current_amount)
            index += 1

        assert last_quote is not None
        return QuoteResponse(
            provider="multi",
            from_asset=from_asset.lower(),
            to_asset=to_asset.lower(),
            input_amount=amount,
            output_amount=self._format_human_output(to_asset.lower(), current_amount),
            output_amount_min=last_quote.get("output_amount_min"),
            price_impact_pct=last_quote.get("price_impact_pct"),
            execution="multi_step",
            route_kind="tcc_extended",
            step_count=len(legs),
        )

    def _format_human_output(self, asset: str, amount: str) -> str:
        if asset != "tcc":
            return amount
        try:
            value = Decimal(amount.replace(",", "."))
        except (InvalidOperation, ValueError):
            return amount
        if value < Decimal("1000000"):
            return amount
        human = value / Decimal("1000000000")
        text = f"{human:.9f}".rstrip("0").rstrip(".")
        return text or "0"

    async def build_step(
        self,
        *,
        from_asset: str,
        to_asset: str,
        amount: str,
        step_order: int,
        slippage_bps: int,
        wallets: WalletAddresses,
    ) -> BuildStepResponse:
        self._validate_amount(amount)
        legs = plan_route(from_asset, to_asset)
        if not legs:
            raise ValueError("pair_unavailable")
        if step_order < 1 or step_order > len(legs):
            raise ValueError("invalid_step_order")

        leg = legs[step_order - 1]
        wallets_dict = wallets.model_dump(exclude_none=True)
        swap_from, swap_to, swap_step = self._swap_leg_mapping(
            leg, from_asset, to_asset
        )

        if swap_step is not None:
            result = await swap_client.build_step(
                from_asset=swap_from,
                to_asset=swap_to,
                amount=amount,
                step_order=swap_step,
                slippage_bps=slippage_bps,
                wallets=wallets_dict,
            )
            return self._build_step_from_swap(
                result,
                leg=leg,
                step_order=step_order,
                total_steps=len(legs),
                amount=amount,
            )

        wallet = self._wallet_for_asset(swap_from, None, wallets)
        if not wallet:
            raise ValueError(f"missing_wallet_{swap_from}")

        result = await swap_client.build(
            from_asset=swap_from,
            to_asset=swap_to,
            amount=amount,
            slippage_bps=slippage_bps,
            wallet_address=wallet,
            wallets=wallets_dict,
        )
        return self._build_step_from_swap(
            result,
            leg=leg,
            step_order=step_order,
            total_steps=len(legs),
            amount=amount,
            default_action="swap",
        )

    def _build_step_from_swap(
        self,
        result: dict,
        *,
        leg: PlannedLeg,
        step_order: int,
        total_steps: int,
        amount: str,
        default_action: str | None = None,
    ) -> BuildStepResponse:
        payload = result.get("payload") or result
        if not isinstance(payload, dict):
            payload = {}
        return BuildStepResponse(
            step_order=int(result.get("step_order") or step_order),
            action=str(result.get("action") or default_action or leg.action),
            provider=str(result.get("provider") or leg.provider),
            from_asset=str(result.get("from_asset") or leg.from_asset),
            to_asset=str(result.get("to_asset") or leg.to_asset),
            input_amount=str(result.get("input_amount") or amount),
            payload=payload,
            total_steps=int(result.get("total_steps") or total_steps),
            wait_hint=result.get("wait_hint"),
            order_id=result.get("order_id"),
        )

    def _swap_leg_mapping(
        self,
        leg: PlannedLeg,
        from_asset: str,
        to_asset: str,
    ) -> tuple[str, str, int | None]:
        delegate = leg.delegate
        if delegate == "swap_tcc_eth_step1":
            return "tcc", "eth", 1
        if delegate == "swap_tcc_eth_step2":
            return "tcc", "eth", 2
        if delegate == "swap_eth_btc":
            return "eth", "btc", None
        if delegate == "swap_btc_eth":
            return "btc", "eth", None
        if delegate == "swap_eth_tcc":
            return "eth", "tcc", 1
        if delegate == "swap_eth_sol":
            return "eth", "sol", None
        if delegate == "swap_sol_eth":
            return "sol", "eth", None
        raise ValueError("unsupported_delegate")

    def _wallet_for_asset(
        self,
        asset: str,
        wallet_address: str | None,
        wallets: WalletAddresses | None,
    ) -> str | None:
        if asset in {"tcc", "wton"} and wallets and wallets.ton:
            return wallets.ton
        if asset in {"eth", "wton"} and wallets and wallets.evm:
            return wallets.evm
        if asset == "btc" and wallets and wallets.btc:
            return wallets.btc
        if asset == "sol" and wallets and wallets.solana:
            return wallets.solana
        return wallet_address

    def _validate_amount(self, amount: str) -> None:
        try:
            value = Decimal(amount.strip().replace(",", "."))
        except (InvalidOperation, AttributeError) as exc:
            raise ValueError("invalid_amount") from exc
        if value <= 0:
            raise ValueError("invalid_amount")


bridge_service = BridgeService()

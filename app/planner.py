from __future__ import annotations

from dataclasses import dataclass

from .assets import BridgeAsset, is_supported_pair, parse_asset


@dataclass(frozen=True)
class PlannedLeg:
    order: int
    action: str
    chain: str
    provider: str
    description: str
    from_asset: str
    to_asset: str
    delegate: str


def plan_route(from_asset: str, to_asset: str) -> list[PlannedLeg]:
    src = parse_asset(from_asset)
    dst = parse_asset(to_asset)
    if not is_supported_pair(src, dst):
        return []

    if src == BridgeAsset.tcc and dst == BridgeAsset.btc:
        return _tcc_to_btc()
    if src == BridgeAsset.btc and dst == BridgeAsset.tcc:
        return _btc_to_tcc()
    if src == BridgeAsset.tcc and dst == BridgeAsset.sol:
        return _tcc_to_sol()
    if src == BridgeAsset.sol and dst == BridgeAsset.tcc:
        return _sol_to_tcc()
    return []


def _tcc_to_btc() -> list[PlannedLeg]:
    return [
        PlannedLeg(
            order=1,
            action="bridge",
            chain="cross",
            provider="TON Bridge",
            description="Bridge TCC → WTON on Ethereum",
            from_asset="tcc",
            to_asset="wton",
            delegate="swap_tcc_eth_step1",
        ),
        PlannedLeg(
            order=2,
            action="swap",
            chain="evm",
            provider="0x",
            description="Swap WTON → ETH",
            from_asset="wton",
            to_asset="eth",
            delegate="swap_tcc_eth_step2",
        ),
        PlannedLeg(
            order=3,
            action="swap",
            chain="cross",
            provider="Symbiosis",
            description="Swap ETH → BTC",
            from_asset="eth",
            to_asset="btc",
            delegate="swap_eth_btc",
        ),
    ]


def _btc_to_tcc() -> list[PlannedLeg]:
    return [
        PlannedLeg(
            order=1,
            action="swap",
            chain="cross",
            provider="Symbiosis",
            description="Swap BTC → ETH",
            from_asset="btc",
            to_asset="eth",
            delegate="swap_btc_eth",
        ),
        PlannedLeg(
            order=2,
            action="bridge",
            chain="cross",
            provider="TON Bridge",
            description="Bridge ETH → TCC on TON",
            from_asset="eth",
            to_asset="tcc",
            delegate="swap_eth_tcc",
        ),
    ]


def _tcc_to_sol() -> list[PlannedLeg]:
    return [
        PlannedLeg(
            order=1,
            action="bridge",
            chain="cross",
            provider="TON Bridge",
            description="Bridge TCC → WTON on Ethereum",
            from_asset="tcc",
            to_asset="wton",
            delegate="swap_tcc_eth_step1",
        ),
        PlannedLeg(
            order=2,
            action="swap",
            chain="evm",
            provider="0x",
            description="Swap WTON → ETH",
            from_asset="wton",
            to_asset="eth",
            delegate="swap_tcc_eth_step2",
        ),
        PlannedLeg(
            order=3,
            action="bridge",
            chain="cross",
            provider="deBridge",
            description="Bridge ETH → SOL",
            from_asset="eth",
            to_asset="sol",
            delegate="swap_eth_sol",
        ),
    ]


def _sol_to_tcc() -> list[PlannedLeg]:
    return [
        PlannedLeg(
            order=1,
            action="bridge",
            chain="cross",
            provider="deBridge",
            description="Bridge SOL → ETH",
            from_asset="sol",
            to_asset="eth",
            delegate="swap_sol_eth",
        ),
        PlannedLeg(
            order=2,
            action="bridge",
            chain="cross",
            provider="TON Bridge",
            description="Bridge ETH → TCC on TON",
            from_asset="eth",
            to_asset="tcc",
            delegate="swap_eth_tcc",
        ),
    ]

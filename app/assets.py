from enum import Enum


class BridgeAsset(str, Enum):
    tcc = "tcc"
    btc = "btc"
    sol = "sol"
    eth = "eth"


SUPPORTED_PAIRS: frozenset[tuple[BridgeAsset, BridgeAsset]] = frozenset(
    {
        (BridgeAsset.tcc, BridgeAsset.btc),
        (BridgeAsset.btc, BridgeAsset.tcc),
        (BridgeAsset.tcc, BridgeAsset.sol),
        (BridgeAsset.sol, BridgeAsset.tcc),
    }
)


def parse_asset(value: str) -> BridgeAsset:
    normalized = value.strip().lower()
    try:
        return BridgeAsset(normalized)
    except ValueError as exc:
        raise ValueError("unsupported_asset") from exc


def is_supported_pair(src: BridgeAsset, dst: BridgeAsset) -> bool:
    return (src, dst) in SUPPORTED_PAIRS

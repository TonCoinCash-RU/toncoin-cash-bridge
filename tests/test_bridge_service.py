from app.assets import is_supported_pair, parse_asset
from app.bridge_service import bridge_service


def test_supported_pairs():
    assert is_supported_pair(parse_asset("tcc"), parse_asset("btc"))
    assert is_supported_pair(parse_asset("sol"), parse_asset("tcc"))
    assert not is_supported_pair(parse_asset("btc"), parse_asset("sol"))


def test_route_tcc_btc():
    route = bridge_service.route("tcc", "btc")
    assert route.available is True
    assert route.execution == "multi_step"
    assert route.step_count == 3


def test_route_same_asset_rejected():
    route = bridge_service.route("tcc", "tcc")
    assert route.available is False
    assert route.hint_key == "same_asset"


def test_route_unsupported():
    route = bridge_service.route("btc", "sol")
    assert route.available is False

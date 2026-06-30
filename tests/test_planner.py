from app.planner import plan_route


def test_tcc_btc_plan_has_three_legs():
    legs = plan_route("tcc", "btc")
    assert len(legs) == 3
    assert legs[0].provider == "TON Bridge"
    assert legs[1].provider == "0x"
    assert legs[2].provider == "Symbiosis"


def test_btc_tcc_plan_has_two_legs():
    legs = plan_route("btc", "tcc")
    assert len(legs) == 2
    assert legs[0].from_asset == "btc"
    assert legs[1].to_asset == "tcc"


def test_tcc_sol_plan():
    legs = plan_route("tcc", "sol")
    assert len(legs) == 3
    assert legs[-1].provider == "deBridge"


def test_sol_tcc_plan():
    legs = plan_route("sol", "tcc")
    assert len(legs) == 2


def test_unsupported_pair_empty():
    assert plan_route("btc", "sol") == []

from unittest.mock import AsyncMock, patch

import pytest

from app.bridge_service import bridge_service
from app.schemas import WalletAddresses


@pytest.mark.asyncio
@patch("app.bridge_service.swap_client.quote", new_callable=AsyncMock)
async def test_quote_btc_tcc_chains_legs(mock_quote):
    mock_quote.side_effect = [
        {"output_amount": "0.5", "output_amount_min": "0.49"},
        {"output_amount": "42.0", "output_amount_min": "41.0"},
    ]
    wallets = WalletAddresses(
        ton="EQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAM9c",
        evm="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        btc="bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
    )
    result = await bridge_service.quote(
        from_asset="btc",
        to_asset="tcc",
        amount="0.001",
        slippage_bps=100,
        wallet_address=None,
        wallets=wallets,
    )
    assert result.output_amount == "42.0"
    assert mock_quote.await_count == 2
    assert mock_quote.await_args_list[0].kwargs["from_asset"] == "btc"
    assert mock_quote.await_args_list[1].kwargs["to_asset"] == "tcc"

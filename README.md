# toncoin-cash-bridge

Микросервис **расширенных кросс-чейн маршрутов** для пар с TCC, которые не покрывает `toncoin-cash-swap`:

| Пара | Маршрут (in-app, multi-step) |
|------|------------------------------|
| TCC → BTC | TON Bridge → 0x (WTON→ETH) → Symbiosis (ETH→BTC) |
| BTC → TCC | Symbiosis (BTC→ETH) → TON Bridge (ETH→TCC) |
| TCC → SOL | TON Bridge → 0x (WTON→ETH) → deBridge (ETH→SOL) |
| SOL → TCC | deBridge (SOL→ETH) → TON Bridge (ETH→TCC) |

Каждый шаг подписывается в кошельке приложения. Сервис **не открывает внешние сайты** — только планирует маршрут и делегирует сборку транзакций в `toncoin-cash-swap`.

## API (порт 8086)

Все эндпоинты (кроме `/healthz`) требуют заголовок `x-api-key`.

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/healthz` | Health check |
| GET | `/bridge/assets` | TCC, BTC, SOL |
| POST | `/bridge/route` | План multi-step маршрута |
| POST | `/bridge/quote` | Сквозная котировка (через swap API) |
| POST | `/bridge/build_step` | Сборка одного шага для подписи в приложении |

### Пример: маршрут TCC → BTC

```bash
curl -sS -X POST http://127.0.0.1:8086/bridge/route \
  -H "x-api-key: $BRIDGE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"from_asset":"tcc","to_asset":"btc"}'
```

### Пример: шаг 1 (мост TCC → WTON)

```json
{
  "from_asset": "tcc",
  "to_asset": "btc",
  "amount": "10",
  "step_order": 1,
  "slippage_bps": 100,
  "wallets": {
    "ton": "EQ...",
    "evm": "0x...",
    "btc": "bc1..."
  }
}
```

## Локальный запуск

```bash
cp .env.example .env
# BRIDGE_API_KEY и SWAP_API_KEY (тот же, что у toncoin-cash-swap)
# SWAP_API_BASE=http://127.0.0.1:8085

pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8086
```

## Деплой на VPS

1. Клонировать в `/opt/toncoin-cash-bridge`.
2. `.env` из `.env.example`: `BRIDGE_API_KEY`, `SWAP_API_BASE`, `SWAP_API_KEY`.
3. Добавить сервис в `/opt/docker-compose.yml` (порт `127.0.0.1:8086:8086`).
4. Nginx: `location /bridge/` → `http://127.0.0.1:8086/bridge/`.
5. Пересобрать: `bash /opt/deploy/update-vps.sh`.

## Flutter (следующий шаг)

В `config/prod.json`:

```json
{
  "BRIDGE_API_BASE": "https://api.toncoincash.ru/bridge",
  "BRIDGE_API_KEY": "..."
}
```

Экран обмена для пар TCC↔BTC / TCC↔SOL будет вызывать этот API вместо fallback с внешними ссылками.

## Тесты

```bash
pytest tests/
```

## Связанные репозитории

- [toncoin-cash-swap](https://github.com/TonCoinCash-RU/toncoin-cash-swap) — DEX, мост TON↔EVM, Symbiosis BTC, deBridge
- [toncoin_cash](https://github.com/TonCoinCash-RU/toncoin_cash) — Flutter-кошелёк

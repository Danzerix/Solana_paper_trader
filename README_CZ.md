# Solana Paper Trader – vývojový základ

Bezpečný prototyp pro **historický backtesting**. Neprovádí skutečné obchody, nepřipojuje peněženku a neobsahuje správu privátních klíčů. Není to hotový AI trader ani investiční doporučení.

## Obsah
- Python + FastAPI backend
- SQLite historie běhů
- SMA backtest bez look-ahead bias (signál z uzavřené svíčky se provede až na další)
- modelované poplatky, skluz, stop-loss a take-profit
- mobilní webový dashboard
- syntetické ukázkové CSV (není to skutečná tržní historie)

## Spuštění
Vyžaduje Python 3.11+.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Otevři `http://IP_SERVERU:8000`. Pro přístup z internetu je před nasazením nutné doplnit autentizaci, HTTPS a firewall. Tento prototyp zatím nevystavuj veřejně.

## CSV
Sloupce: `timestamp,open,high,low,close,volume`; timestamp v ISO-8601, ceny/objem číselné a nezáporné. Svíčky se seřadí podle času. Ukázkový soubor `data/sample_synthetic.csv` je pouze syntetický test.

## Výchozí parametry
Virtuální kapitál 1 USD; SMA 5/20; poplatek 0,5 % a skluz 0,2 % na každou stranu; stop-loss 5 %; take-profit 10 %; velikost pozice max. 25 % původního kapitálu. Nejde o optimalizované parametry.

## API
- `GET /api/health`
- `GET /api/config`
- `POST /api/backtest` (multipart CSV; initial_capital, fee_pct a slippage_pct)
- `GET /api/runs`

Historický výsledek nezaručuje budoucí výnos. Před jakýmkoli živým paper tradingem je nutné ověřit kvalitu dat, otestovat strategii mimo vzorek a doplnit zabezpečení.

**Nikdy neposílej seed phrase ani privátní klíče do chatu.**

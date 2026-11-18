from dataclasses import dataclass, asdict
import pandas as pd

@dataclass
class Config:
    initial_capital: float = 1.0
    fee_pct: float = 0.005
    slippage_pct: float = 0.002
    fast_sma: int = 5
    slow_sma: int = 20
    stop_loss_pct: float = 0.05
    take_profit_pct: float = 0.10
    max_position_pct: float = 0.25

def run_backtest(df: pd.DataFrame, cfg: Config):
    required = {"timestamp", "open", "high", "low", "close", "volume"}
    if not required.issubset(df.columns):
        raise ValueError("CSV musí obsahovat timestamp,open,high,low,close,volume")
    df = df.copy()
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="raise")
        if (df[col] < 0).any():
            raise ValueError(f"Sloupec {col} obsahuje záporné hodnoty")
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="raise")
    df = df.sort_values("timestamp").drop_duplicates("timestamp").reset_index(drop=True)
    if len(df) < cfg.slow_sma + 2:
        raise ValueError(f"Je potřeba alespoň {cfg.slow_sma + 2} svíček")
    if (df["close"] <= 0).any():
        raise ValueError("Závěrečné ceny musí být kladné")
    df["fast"] = df.close.rolling(cfg.fast_sma).mean()
    df["slow"] = df.close.rolling(cfg.slow_sma).mean()
    cash, units, entry = cfg.initial_capital, 0.0, None
    trades, equity = [], []
    for i in range(1, len(df)):
        prev, row = df.iloc[i-1], df.iloc[i]
        price = float(row.open)
        if units > 0:
            reason = None
            stop, target = entry * (1-cfg.stop_loss_pct), entry * (1+cfg.take_profit_pct)
            # Pokud svíčka zasáhne SL i TP, konzervativně počítáme SL.
            if float(row.low) <= stop:
                reason, raw_exit = "stop_loss", stop
            elif float(row.high) >= target:
                reason, raw_exit = "take_profit", target
            elif pd.notna(prev.fast) and pd.notna(prev.slow) and prev.fast < prev.slow:
                reason, raw_exit = "signal", price
            if reason:
                fill = raw_exit * (1-cfg.slippage_pct)
                proceeds = units * fill * (1-cfg.fee_pct)
                cost_basis = units * entry
                pnl = proceeds - cost_basis
                cash += proceeds
                trades.append({"side":"SELL", "time":row.timestamp.isoformat(), "price":fill, "reason":reason, "pnl":pnl})
                units, entry = 0.0, None
        elif pd.notna(prev.fast) and pd.notna(prev.slow) and prev.fast > prev.slow:
            budget = min(cash, cfg.initial_capital * cfg.max_position_pct)
            if budget > 0:
                fill = price * (1+cfg.slippage_pct)
                units = budget * (1-cfg.fee_pct) / fill
                cash -= budget
                entry = fill
                trades.append({"side":"BUY", "time":row.timestamp.isoformat(), "price":fill, "reason":"sma_signal", "pnl":None})
        equity.append({"time":row.timestamp.isoformat(), "equity":cash + units*float(row.close)})
    final_equity = cash + units*float(df.iloc[-1].close)
    ret = (final_equity/cfg.initial_capital-1)*100
    sells = [t for t in trades if t["side"] == "SELL"]
    wins = sum(1 for t in sells if (t["pnl"] or 0) > 0)
    peak, max_dd = cfg.initial_capital, 0.0
    for point in equity:
        peak = max(peak, point["equity"])
        if peak:
            max_dd = max(max_dd, (peak-point["equity"])/peak*100)
    return {"config":asdict(cfg), "initial_capital":cfg.initial_capital,
            "final_equity":round(final_equity,8), "return_pct":round(ret,4),
            "closed_trades":len(sells), "win_rate_pct":round(wins/len(sells)*100,2) if sells else None,
            "max_drawdown_pct":round(max_dd,2), "open_position":units>0,
            "trades":trades, "equity_curve":equity, "bars":len(df),
            "data_notice":"Výsledek platí pouze pro dodané CSV; ukázková data jsou syntetická."}

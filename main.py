from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import pandas as pd, sqlite3, json, uuid, io
from .backtest import Config, run_backtest
ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "runs.sqlite3"
app = FastAPI(title="Solana Paper Trader", version="0.1.0")
app.mount("/static", StaticFiles(directory=ROOT/"static"), name="static")
def init_db():
    with sqlite3.connect(DB) as c:
        c.execute("CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, created_at TEXT DEFAULT CURRENT_TIMESTAMP, result TEXT NOT NULL)")
init_db()
@app.get("/", response_class=HTMLResponse)
def home():
    return (ROOT/"static"/"index.html").read_text(encoding="utf-8")
@app.get("/api/health")
def health(): return {"status":"ok", "mode":"backtest_only", "real_trading":False}
@app.get("/api/config")
def config(): return {"defaults":Config().__dict__, "mode":"historical_backtest_only"}
@app.get("/api/runs")
def runs():
    with sqlite3.connect(DB) as c:
        rows=c.execute("SELECT id,created_at,result FROM runs ORDER BY created_at DESC LIMIT 20").fetchall()
    return [{"id":r[0],"created_at":r[1],"result":json.loads(r[2])} for r in rows]
@app.post("/api/backtest")
async def backtest(file: UploadFile=File(...), initial_capital:float=Form(1.0), fee_pct:float=Form(0.005), slippage_pct:float=Form(0.002)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(400,"Nahraj CSV soubor.")
    if initial_capital <= 0 or not (0 <= fee_pct < .1) or not (0 <= slippage_pct < .1):
        raise HTTPException(400,"Neplatné parametry.")
    try:
        content=await file.read()
        if len(content)>5_000_000: raise ValueError("CSV je příliš velké (limit 5 MB).")
        df=pd.read_csv(io.BytesIO(content))
        result=run_backtest(df, Config(initial_capital=initial_capital, fee_pct=fee_pct, slippage_pct=slippage_pct))
        rid=str(uuid.uuid4())
        with sqlite3.connect(DB) as c:
            c.execute("INSERT INTO runs(id,result) VALUES(?,?)",(rid,json.dumps(result)))
        return {"id":rid,"result":result}
    except Exception as e:
        raise HTTPException(400,str(e))

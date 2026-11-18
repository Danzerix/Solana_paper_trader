import pandas as pd
from app.backtest import Config, run_backtest

def test_backtest_returns_expected_fields():
    n=80
    close=[1+i*.001 for i in range(n)]
    df=pd.DataFrame({'timestamp':pd.date_range('2025-01-01',periods=n,freq='h',tz='UTC'),'open':close,'high':[x*1.01 for x in close],'low':[x*.99 for x in close],'close':close,'volume':[1000]*n})
    result=run_backtest(df,Config())
    assert result['initial_capital']==1.0
    assert result['bars']==n
    assert 'final_equity' in result

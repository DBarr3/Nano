# Nano Strategy Library

The community strategy library for Nano — think TradingView's Pine public
library, but every entry is a **compilable, replayable, risk-gated artifact**.
Each strategy is a pair:

- `<name>.nano` — the human-readable source
- `<name>_ir.json` — the canonical Nano IR it compiles to, byte-diffable and
  verified by the conformance suite (`tests/test_library.py`)

Nothing here places trades. A library strategy only **emits intents**
(`{"intent": "BUY", "asset": "BTCUSD", "confidence": 0.85}`); your risk engine
/ execution gate decides whether execution is allowed. That separation is
structural: the IR has no order or exchange primitive, and emitting intents
requires `intent.emit` in the strategy's effect manifest.

## Category map

| Category | Strategies |
|---|---|
| `momentum/` | `rsi_oversold_reversal`, `stochastic_oversold`, `williams_r_reversal`, `roc_momentum` |
| `mean_reversion/` | `bollinger_band_touch`, `zscore_reversion`, `cci_extreme` |
| `trend/` | `golden_cross`, `macd_histogram_flip`, `donchian_breakout` |
| `volatility/` | `atr_volatility_halt`, `bb_squeeze_breakout` |
| `volume/` | `volume_spike_confirmation`, `obv_trend` |
| `risk/` | `max_drawdown_breaker` |

## Pine -> Nano translation conventions

Nano v0.1.0 is deliberately tiny: conditions compare **named signal series**
against numbers. Signals are injected at runtime by the host data feed — the
language never computes indicators. Anything Pine derives in-script (crosses,
spreads, band math) becomes a *named signal* with a documented convention:

| Pine expression | Nano signal | Convention |
|---|---|---|
| `ta.rsi(close, 14)` | `RSI(14)` | raw RSI, 0..100 |
| `ta.stoch(...)` %K | `STOCH_K(14)` | raw %K, 0..100 |
| `ta.wpr(14)` | `WILLR_POS(14)` | Williams %R **+ 100** (0..100; number literals are non-negative) |
| `ta.roc(close, 10)` | `ROC(10)` | percent change over the window |
| Bollinger %B | `BB_PCT_B(20)` | `(close - lower) / (upper - lower)` |
| Bollinger width | `BB_WIDTH(20)` | `(upper - lower) / middle * 100` |
| z-score | `ZSCORE_NEG(20)` | **negated** z-score: `-(close - sma) / stdev` |
| `ta.cci(20)` | `CCI_NEG(20)` | **negated** CCI (>= 100 is the classic < -100 zone) |
| `ta.crossover(sma50, sma200)` | `SMA_SPREAD(50)` | `SMA(50) - SMA(200)`; > 0 = post-golden-cross regime |
| MACD histogram | `MACD_HIST(9)` | MACD line - signal line |
| Donchian breakout | `DONCHIAN_POS(20)` | `(close - lower) / (upper - lower)`; >= 1 = new channel high |
| `ta.atr(14) / close` | `ATR_PCT(14)` | ATR as percent of price |
| `ta.mom(close, 10)` | `MOM(10)` | `close - close[10]` |
| volume spike | `VOL_RATIO(20)` | `volume / sma(volume, 20)` |
| OBV trend | `OBV_SLOPE(20)` | linear-regression slope of OBV |
| equity drawdown | `DRAWDOWN` | portfolio drawdown, percent |

Two rules fall out of the grammar:

1. **Non-negative literals.** Nano number literals cannot be negative, so
   signals with negative natural ranges are shifted (`WILLR_POS`) or negated
   (`ZSCORE_NEG`, `CCI_NEG`) by the feed. Document the transform in a `//`
   comment next to the condition.
2. **The `(N)` argument is documentation.** `RSI(14)` and `RSI` compile to the
   same `Condition` node; the lookback lives in the feed's signal definition.
   Keep it in source anyway — it is the contract with the data feed.

## How intents flow

```
market frames -> Nano runtime -> Intent(BUY/SELL/EXECUTE/PAUSE/OBSERVE)
             -> your risk engine / execution gate -> execution decision
```

The runtime is a pure function of (IR, MarketFrame): identical inputs replay
bit-identically, so every library strategy is backtestable and auditable by
construction. `PAUSE`/`OBSERVE` intents (see `risk/`, `volatility/`) are how a
strategy asks the downstream gate to halt or watch; an optional `agent Name`
declaration names the behavior block that should take over.

## Contributing a strategy

1. Pick a category folder (or propose a new one).
2. Write `<name>.nano` within the v0.1.0 grammar: one `every` block, one `if`
   rule (and-chains allowed), actions from `buy/sell/execute/pause/observe`.
   Document every derived-signal convention in a `//` comment.
3. Generate its partner: `python -c "from nano.compiler import compile_to_dict; ..."`
   and save the result as `<name>_ir.json` (same formatting style as existing
   entries).
4. Run `python -m pytest tests/test_library.py -q` — the conformance suite
   globs this directory, so your pair is picked up automatically. The pair
   must compile bit-identically and the IR must round-trip; nothing merges
   without a green suite.

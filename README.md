# day_trade_algo

Monte Carlo simulation of a futures prop-firm evaluation account with a
trailing maximum loss limit (MLL) that is enforced as a hard intraday limit.

If equity touches the MLL floor at any point in the session, open unrealized
losses included, the account is breached, even if the day closes above the
floor. Because of this, the simulation checks every open trade's maximum
adverse excursion (MAE) against the floor. It does not just check the
closing balance.

## Model

`flex_v3.py` simulates trading day by day until the account passes, breaches,
or runs out of days.

| Parameter | Value | Meaning |
|---|---|---|
| `START` | $100,000 | starting balance |
| `TARGET` | $6,000 | profit needed to pass |
| `MLL` | $3,000 | trailing drawdown from the highest close |
| `TRAIL_CAP` | $100,100 | floor stops trailing once it reaches this level |
| `DAILY_LOSS_CAP` | $500 | no new trades once the day's realized loss reaches this |
| `CUSHION` | 1.04 | slack on the consistency rule |
| `COMMISSION` | $15 | per trade |
| `SMALL_WIN_SHARE` | 0.60 | share of winners paying 2R (the rest pay 1.5R) |
| `WINNER_MAE_MAX` | 0.6 | a winner can go up to 60% of the stop distance against you first |
| `MAX_DAYS` | 2,000 | run counts as stalled after this |

- Each day draws a Poisson number of signals (default 1.5 per day).
- A loser goes all the way to the stop and loses 1R.
- A winner first drifts against you by a random fraction of the stop, then pays out.
- To pass, an account must reach the profit target. Its best day must also be
  no more than 50% of total profit (times `CUSHION`).

## Output

Each scenario runs 10,000 simulated accounts. The script prints:

1. Pass rates with closing-balance-only breach checks vs. hard intraday checks
   at a 65% win rate, for risk per trade from $250 to $2,000 (with the
   equivalent NQ mini count at a 30-point stop).
2. Pass and breach rates by win rate (55% to 70%) at $250 risk.
3. How many NQ minis or MNQ micros at a given stop size put the
   account at the floor on a single losing trade.

## Usage

```
pip install -r requirements.txt
python flex_v3.py
```

The random generator is seeded (`default_rng(3)`), so results are
reproducible.

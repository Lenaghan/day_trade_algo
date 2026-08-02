"""
Corrected again: Lucid support confirms the MLL is a HARD limit.
Equity dropping below it at any moment during the session, including
in open unrealized PnL, is a breach. Closing above does not undo it.

So breach must be checked on running intraday equity, not on the
closing balance. Maximum adverse excursion (MAE) of each open trade
is now load-bearing.
"""
import numpy as np
from collections import Counter

START = 100_000
TARGET = 6_000
MLL = 3_000
TRAIL_CAP = 100_100
CUSHION = 1.04
DAILY_LOSS_CAP = 500
COMMISSION = 15.0
SMALL_WIN_SHARE = 0.60
MAX_DAYS = 2_000

# a winner still goes against you before it works
WINNER_MAE_MAX = 0.6      # fraction of stop distance

RNG = np.random.default_rng(3)


def run(win_rate, risk, sig_per_day, intraday_breach=True, rng=RNG):
    balance = START
    peak_close = START
    floor = min(peak_close - MLL, TRAIL_CAP)
    days = []

    for _ in range(MAX_DAYS):
        n = rng.poisson(sig_per_day)
        realized = 0.0
        for _ in range(n):
            if realized <= -DAILY_LOSS_CAP:
                break

            loser = rng.random() >= win_rate
            if loser:
                mae = risk                       # taken to the stop
                r = 2.0
            else:
                mae = rng.uniform(0, WINNER_MAE_MAX) * risk
                r = 0.5 if rng.random() < SMALL_WIN_SHARE else 1.5

            # equity trough while this trade is open
            if intraday_breach:
                trough = balance + realized - mae
                if trough <= floor:
                    return "breach", len(days) + 1

            realized += r * risk - COMMISSION

        balance += realized
        days.append(realized)

        if balance <= floor:
            return "breach", len(days)
        if balance > peak_close:
            peak_close = balance
            floor = min(peak_close - MLL, TRAIL_CAP)

        total = balance - START
        if total >= TARGET and max(days) <= 0.50 * total * CUSHION:
            return "pass", len(days)

    return "stalled", MAX_DAYS


def tally(wr, risk, sig=1.5, intraday=True, n=10_000):
    c = Counter()
    for _ in range(n):
        c[run(wr, risk, sig, intraday)[0]] += 1
    return {k: v / n for k, v in c.items()}


print("EFFECT OF THE HARD INTRADAY LIMIT (win 65%, 1.5 signals/day)")
print(f"{'risk':>7} {'minis @30pt':>12} {'pass EOD-only':>14} {'pass intraday':>14} {'breach':>8}")
for risk in [250, 500, 750, 1000, 1500, 2000]:
    eod = tally(0.65, risk, intraday=False)
    intr = tally(0.65, risk, intraday=True)
    minis = risk / (30 * 20)
    print(f"${risk:>6} {minis:>12.1f} {eod.get('pass',0):>13.1%} "
          f"{intr.get('pass',0):>13.1%} {intr.get('breach',0):>7.1%}")

print("\nBY WIN RATE, hard intraday limit, risk $250")
print(f"{'win':>6} {'pass':>8} {'breach':>8}")
for wr in [0.55, 0.60, 0.65, 0.70]:
    t = tally(wr, 250)
    print(f"{wr:>5.0%} {t.get('pass',0):>7.1%} {t.get('breach',0):>7.1%}")

print("\nSINGLE-TRADE WIPEOUT THRESHOLD")
print("buffer is a flat $3,000 until the account clears $103,100")
for stop_pts in [20, 25, 30, 40]:
    print(f"  {stop_pts:>2}pt stop: {3000/(stop_pts*20):>4.1f} NQ minis "
          f"or {3000/(stop_pts*2):>5.1f} MNQ micros reaches the floor "
          f"on one trade")

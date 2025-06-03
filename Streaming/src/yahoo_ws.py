import yliveticker
import time
from collections import deque

msg_times = deque(maxlen=1000)  # Store timestamps of recent messages

def on_new_msg(ws, msg):
    now = time.time()
    msg_times.append(now)
    # Calculate messages in the last second
    one_sec_ago = now - 1
    freq = sum(1 for t in msg_times if t >= one_sec_ago)
    print(f"Msg: {msg}")
    print(f"Messages in the last second: {freq}")

# Subscribe to Australian tickers
yliveticker.YLiveTicker(
    on_ticker=on_new_msg,
    ticker_names=["CBA.AX", "BHP.AX", "WBC.AX", "NAB.AX", "ANZ.AX"]
)

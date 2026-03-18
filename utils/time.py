import time


def generate_ts() -> str:
    return f"{time.time_ns() / 1e9:.6f}"

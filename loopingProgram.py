import time
import sys

def loop_for_n_seconds(n: float):
    start = time.time()
    while time.time() - start < n:
        # sleep briefly to avoid pegging 100% CPU
        time.sleep(0.1)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <seconds>")
        sys.exit(1)
    try:
        seconds = float(sys.argv[1])
    except ValueError:
        print("Please provide a numeric value for seconds.")
        sys.exit(1)

    print(f"Looping for {seconds} seconds...")
    loop_for_n_seconds(seconds)
    print("Done.")

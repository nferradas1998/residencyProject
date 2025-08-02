import threading
import time
from queue import Queue

# Producer-Consumer

def producer_consumer(buffer_size=5, n_items=20):
    buffer = Queue(maxsize=buffer_size)
    
    def producer():
        for i in range(n_items):
            buffer.put(i)
            print(f"Produced {i}")
            time.sleep(0.1)
        print("Producer done")

    def consumer():
        for _ in range(n_items):
            item = buffer.get()
            print(f"Consumed {item}")
            time.sleep(0.2)
        print("Consumer done")

    t1 = threading.Thread(target=producer)
    t2 = threading.Thread(target=consumer)
    t1.start(); t2.start()
    t1.join(); t2.join()

# Dining Philosophers

def dining_philosophers(n=5, eat_limit=3):
    forks = [threading.Lock() for _ in range(n)]
    
    def philosopher(i):
        left, right = forks[i], forks[(i+1)%n]
        for _ in range(eat_limit):
            print(f"Philosopher {i} is thinking")
            time.sleep(0.1)
            with left:
                with right:
                    print(f"Philosopher {i} is eating")
                    time.sleep(0.1)
        print(f"Philosopher {i} done")

    threads = [threading.Thread(target=philosopher, args=(i,)) for i in range(n)]
    for t in threads: t.start()
    for t in threads: t.join()
    print("Dining philosophers complete")
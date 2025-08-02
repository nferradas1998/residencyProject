import time
from collections import deque, OrderedDict

class PageFault(Exception):
    pass

class MemoryManager:
    def __init__(self, total_frames, algorithm='FIFO'):
        self.total_frames = total_frames
        self.algorithm = algorithm.upper()
        self.frames = {}
        self.free_frames = list(range(total_frames))
        self.page_table = {}
        self.load_order = deque()
        self.usage_order = OrderedDict()
        self.page_faults = {}

    def add_process(self, pid):
        print(f"\n[+] Process {pid} added to memory manager.")
        self.page_table[pid] = {}
        self.page_faults[pid] = 0

    def remove_process(self, pid):
        print(f"\n[-] Removing Process {pid} and freeing its memory.")
        for page, frame in list(self.page_table[pid].items()):
            self.free_frames.append(frame)
            self.frames.pop(frame, None)
            try:
                self.load_order.remove((pid, page))
            except ValueError:
                pass
            self.usage_order.pop((pid, page), None)
        self.page_table.pop(pid)
        self.page_faults.pop(pid)
        print("[ok] Memory deallocation complete.\n")

    def access_page(self, pid, page):
        print(f"\n[Access] Process {pid} requests page {page}")
        pt = self.page_table[pid]
        # Hit
        if page in pt:
            frame = pt[page]
            print(f"[HIT] Page {page} is already in frame {frame}")
            if self.algorithm == 'LRU':
                # move to end
                self.usage_order.pop((pid, page), None)
                self.usage_order[(pid, page)] = frame
            return True

        # Fault
        self.page_faults[pid] += 1
        print(f"[FAULT] Page {page} not in memory - PAGE FAULT!")
        # Allocate frame or replace
        if self.free_frames:
            frame = self.free_frames.pop(0)
            print(f"[ALLOC] Free frame {frame} allocated")
        else:
            # choose victim
            if self.algorithm == 'FIFO':
                victim = self.load_order.popleft()
            elif self.algorithm == 'LRU':
                victim = next(iter(self.usage_order))
            else:
                raise ValueError("Unknown algorithm")
            victim_pid, victim_page = victim
            frame = self.page_table[victim_pid].pop(victim_page)
            self.frames.pop(frame)
            print(f"[REPLACE] Evicted page {victim_page} of process {victim_pid} from frame {frame}")
            # remove from trackers
            if self.algorithm == 'FIFO':
                pass  # already popped
            else:
                self.usage_order.pop(victim)

        # load new page
        self.frames[frame] = (pid, page)
        pt[page] = frame
        self.load_order.append((pid, page))
        self.usage_order[(pid, page)] = frame
        print(f"[LOAD] Loaded page {page} into frame {frame}")
        self.print_state()
        raise PageFault(f"PID {pid} page {page} fault -> loaded in frame {frame}")

    def print_state(self):
        print("\n[Memory State]")
        for frame in range(self.total_frames):
            content = self.frames.get(frame, "---")
            if content != "---":
                pid, page = content
                print(f"Frame {frame}: PID {pid}, Page {page}")
            else:
                print(f"Frame {frame}: [FREE]")
        print("[Page Tables]")
        for pid, table in self.page_table.items():
            print(f"PID {pid}: {table}")
        print("")
    def stats(self):
        lines = []
        lines.append(f"Total frames: {self.total_frames}")
        lines.append(f"Algorithm: {self.algorithm}")
        for pid, faults in self.page_faults.items():
            lines.append(f"PID {pid}: {faults} page faults, pages in memory: {list(self.page_table[pid].keys())}")
        return "\n".join(lines)
    

# Run simulation
results = []
access_sequence = [1, 2, 3, 1, 4, 5, 1, 2]

for algorithm in ['FIFO', 'LRU']:
    mm = MemoryManager(total_frames=3, algorithm=algorithm)
    mm.add_process('P1')
    results.append(f"\n--- {algorithm} Simulation ---")
    for page in access_sequence:
        try:
            mm.access_page('P1', page)
        except PageFault as pf:
            results.append(str(pf))
    results.append(mm.stats())
    mm.remove_process('P1')


# Run simulation
access_sequence = [1, 2, 3, 1, 4, 5, 1, 2]

for algorithm in ['FIFO', 'LRU']:
    mm = MemoryManager(total_frames=3, algorithm=algorithm)
    mm.add_process('P1')
    print(f"\n--- {algorithm} Simulation ---")
    for page in access_sequence:
        try:
            mm.access_page('P1', page)
        except PageFault as pf:
            print(pf)
    mm.stats()
    mm.remove_process('P1')
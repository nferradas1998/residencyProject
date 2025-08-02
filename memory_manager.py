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
        self.page_table[pid] = {}
        self.page_faults[pid] = 0

    def remove_process(self, pid):
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

    def access_page(self, pid, page):
        pt = self.page_table[pid]
        # Hit
        if page in pt:
            frame = pt[page]
            if self.algorithm == 'LRU':
                # move to end
                self.usage_order.pop((pid, page), None)
                self.usage_order[(pid, page)] = frame
            return True

        # Fault
        self.page_faults[pid] += 1
        # Allocate frame or replace
        if self.free_frames:
            frame = self.free_frames.pop(0)
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
            # remove from trackers
            if self.algorithm == 'FIFO':
                pass  # already popped
            else:
                self.usage_order.pop(victim)

        # load new page
        self.frames[frame] = (pid, page)
        self.page_table[pid][page] = frame
        self.load_order.append((pid, page))
        self.usage_order[(pid, page)] = frame
        raise PageFault(f"PID {pid} page {page} fault -> loaded in frame {frame}")

    def stats(self):
        lines = []
        lines.append(f"Total frames: {self.total_frames}")
        lines.append(f"Algorithm: {self.algorithm}")
        for pid, faults in self.page_faults.items():
            lines.append(f"PID {pid}: {faults} page faults, pages in memory: {list(self.page_table[pid].keys())}")
        return "\n".join(lines)
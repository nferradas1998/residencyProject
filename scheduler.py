import time
import heapq
import os
import signal
import sys

try:
    import win32api, win32con
    from ctypes import windll
    NtSuspendProcess = windll.ntdll.NtSuspendProcess
    NtResumeProcess  = windll.ntdll.NtResumeProcess
except ImportError:
    win32api = win32con = NtSuspendProcess = NtResumeProcess = None

def suspend_process(proc):
    if sys.platform.startswith('win') and NtSuspendProcess:
        handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, False, proc.pid)
        NtSuspendProcess(handle.handle)
        win32api.CloseHandle(handle)
    else:
        os.kill(proc.pid, signal.SIGSTOP)


def resume_process(proc):
    if sys.platform.startswith('win') and NtResumeProcess:
        handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, False, proc.pid)
        NtResumeProcess(handle.handle)
        win32api.CloseHandle(handle)
    else:
        os.kill(proc.pid, signal.SIGCONT)


class RoundRobinScheduler:
    def __init__(self, jobs, quantum):
        self.jobs = jobs
        self.quantum = quantum ## define quantum as the seconds assigned to each slice

    def run(self):
        for job in self.jobs: ## restart jobs
            if job['proc'].poll() is None:
                suspend_process(job['proc'])

        while True: ## loop until all processes are finished
            alive = [j for j in self.jobs if j['proc'].poll() is None]
            if not alive:
                break

            for job in alive:
                pid = job['proc'].pid
                print(f"Resuming job {job['id']} (PID {pid})")
                resume_process(job['proc'])
                time.sleep(self.quantum)

                if job['proc'].poll() is None:
                    print(f"Suspending job {job['id']} after {self.quantum}s") ## Once time passed, suspend the job to resume the next
                    suspend_process(job['proc'])
                else:
                    print(f"Job {job['id']} completed")

        print("Round-Robin scheduling complete")


class PriorityScheduler:
    def __init__(self, jobs):
        self.jobs = jobs

    def run(self):
        for job in self.jobs:
            if job['proc'].poll() is None:
                suspend_process(job['proc'])

        heap = [(-j['priority'], j) for j in self.jobs if j['proc'].poll() is None] ## initialize the heap based on priority
        heapq.heapify(heap) ## sort the heap.

        while heap: ## iterate through the heap
            neg_p, job = heapq.heappop(heap)
            prio = -neg_p
            proc = job['proc']

            if proc.poll() is not None:
                continue

            print(f"Running job {job['id']} (priority={prio})")
            resume_process(proc)

            while proc.poll() is None:
                higher = [j for j in self.jobs
                          if j['proc'].poll() is None
                          and j['priority'] > prio]
                if higher:
                    pre = higher[0] ## if incoming priority is higher, then pause current job
                    print(f"Preempting job {job['id']} for job {pre['id']}")
                    suspend_process(proc)
                    heapq.heappush(heap, (-prio, job))
                    job = pre
                    prio = job['priority']
                    proc = job['proc']
                    resume_process(proc)
                else:
                    time.sleep(0.5)

            print(f"Job {job['id']} completed")

        print("Priority scheduling complete")
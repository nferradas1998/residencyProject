import os
import sys
import shlex
import signal
import subprocess
import win32api
import win32con
import ctypes
from ctypes import wintypes
from scheduler import RoundRobinScheduler, PriorityScheduler
import threading
import time
import process_sync
from memory_manager import MemoryManager, PageFault
from queue import Queue

ntdll = ctypes.WinDLL("ntdll")

NtSuspendProcess = ntdll.NtSuspendProcess
NtSuspendProcess.restype = wintypes.ULONG
NtSuspendProcess.argtypes = [wintypes.HANDLE]

NtResumeProcess = ntdll.NtResumeProcess
NtResumeProcess.restype = wintypes.ULONG
NtResumeProcess.argtypes = [wintypes.HANDLE]

class Shell:
    def __init__(self):
        self.job_queue = Queue()           # unbounded; or Queue(maxsize=N) to limit # of jobs
        self.jobs_lock  = threading.Lock()
        self.jobs = [] # initialiing job array to help with process management
        self.next_job_id = 1 # initializing first job id as 1 for first job    
        self.current_process = None # initializing current variable as null to track current process
        self.current_cmd = None # initializing current command variable as null to track current command
        self.mm = MemoryManager(total_frames=10, algorithm='LRU') 

        # Define lists of commands that are supported by the OS
        self.builtins = {
            'cd':self.cmd_cd, # change directory
            'pwd':self.cmd_pwd, # print current working diractory
            'exit':self.cmd_exit, # terminate the shell
            'echo':self.cmd_echo, # print specified text to the terminal
            'clear':self.cmd_clear, # clear the terminal screen
            'ls':self.cmd_ls, # list files in the current directory
            'cat':self.cmd_cat, # display contents of a file
            'edit':self.cmd_edit, # edit the contents of a file
            'mkdir':self.cmd_mkdir, # create new directory
            'rmdir':self.cmd_rmdir, # remove empty directory
            'rm':self.cmd_rm, # remove file
            'touch':self.cmd_touch, # create a new empty file or edit timestamp of existing file
            'kill':self.cmd_kill, # terminate process by processId
            'jobs':self.cmd_jobs, # list all background jobs
            'fg':self.cmd_fg, # bring a background job to the foreground
            'bg':self.cmd_bg, # resume stopped job in the background,
            'run':self.cmd_run, # Run a python program
            'pause':self.cmd_pause,
            'srr':  self.cmd_srr,
            'spri': self.cmd_spri,
            'runp': self.cmd_runp,
            'meminit': self.cmd_meminit,
            'memadd':  self.cmd_memadd,
            'memreq':  self.cmd_memreq,
            'memstats': self.cmd_memstats,
        }

    def run(self):
        print("Welcome to Team 4's Operating System! Enter a command to start")
        while True:
            try:
                cwd = os.getcwd()
                line = input(f'{cwd} > ').strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not line:
                continue

            background = line.endswith('&')
            if background:
                line = line[:-1].strip()

            parts = shlex.split(line)
            if not parts:
                continue
            cmd, *args = parts

            if cmd in self.builtins:
                self.builtins[cmd](args)
            else:
                self.launch_cmd(parts, background)

    def launch_cmd(self, parts, background): # method to start the command line shell
        try:
            proc = subprocess.Popen(
                parts,
                preexec_fn=os.setpgrp if hasattr(os, 'setpgrp') else None
            )
        except FileNotFoundError:
            print(f"{parts[0]}: command not found")
            return
        except Exception as e:
            print(f"Error launching '{parts[0]}': {e}")
            return

        self.current_process = proc
        self.current_cmd = ' '.join(parts)

        if background:
            self.jobs.append({
                'id': self.next_job_id,
                'proc': proc,
                'cmd': self.current_cmd,
                'status': 'Running'
            })
            print(f"[{self.next_job_id}] {proc.pid}")
            self.next_job_id += 1
            self.current_process = None
        else:
            proc.wait()
            self.current_process = None

    #============START OF IMPLEMENTATION OF COMMAND FUNCTIONS=================#

    ## Change directory
    def cmd_cd(self, args):
        try:
            os.chdir(args[0] if args else os.path.expanduser('~'))
        except Exception as e:
            print(f"cd: {e}")

    ## print current working directory
    def cmd_pwd(self, args):
        print(os.getcwd())

    
    ## exit the shell
    def cmd_exit(self, args):
        print("Thanks for using Team 4's OS, see you next time")
        sys.exit(0)

    ## print test to the command line
    def cmd_echo(self, args):
        print(' '.join(args))

    ## clear terminal screen
    def cmd_clear(self, args):
        if sys.platform.startswith('win'):
            os.system('cls')
        else:
            os.system('clear')
        print(f"Terminal cleared")


    ## list items in current directory
    def cmd_ls(self, args):
        try:
            curr_dir = "."
            files = []
            entries = os.listdir(curr_dir)
            for entry in entries:
                full_path = os.path.join(curr_dir, entry)
                if os.path.isfile(full_path):
                    files.append(entry)

            for filename in files:
                print(filename)
        except Exception as e:
            print(f"ls: {e}")


    ## print the contents of a file
    def cmd_cat(self, args):
        try:
            with open(args[0], 'r') as f:
                content = f.read()
                print(content)
        except FileNotFoundError:
            print(f"File Not Found")
        except Exception as e:
            print(f"An error occurred: {e}")


    ## edit the contents of a file
    def cmd_edit(self, args):
        filename = args[0]
        try:
            with open(filename, 'r') as f: # try opening file
                existing = f.read().splitlines() 
        except FileNotFoundError:
            existing = [] # if file does not exist, create one
        print("File editor: Enter '.save' to save and exit or '.exit' to cancel.\n")
        for line in existing:
            print(line)
        new_lines = []
        while True:
            try:
                inp = input()
            except (EOFError, KeyboardInterrupt):
                print()
                print("Edit canceled.")
                return
            if inp == '.save':
                try:
                    with open(filename, 'w') as f:
                        f.write('\n'.join(new_lines) + '\n')
                    print(f"File '{filename}' saved.")
                except Exception as e:
                    print(f"edit: failed to save {filename}: {e}")
                return
            elif inp == '.exit':
                print("Edit canceled.")
                return
            else:
                new_lines.append(inp)

    ## Create new directory
    def cmd_mkdir(self, args):
        try:
            os.mkdir(args[0])
            print(f"Directory '{args[0]}' created successfully.")
        except FileExistsError:
            print(f"Directory '{args[0]}' already exists.")
        except OSError as e:
            print(f"Error creating directory: {e}")

    ## remove empty directory
    def cmd_rmdir(self, args):
        try:
            os.rmdir(args[0])
            print(f"Directory '{args[0]}' removed successfully.")
        except FileNotFoundError:
            print(f"Directory '{args[0]}' not found.")
        except OSError as e:
            print(f"Error removing directory: {e}")

    ## Remove file
    def cmd_rm(self, args):
        try:
            os.remove(args[0])
            print(f"File '{args[0]}' removed successfully.")
        except FileNotFoundError:
            print(f"File '{args[0]}' not found.")
        except IsADirectoryError:
            print(f"'{args[0]}' is a directory. Use rmdir to remove directories.")
        except OSError as e:
            print(f"Error removing file: {e}")


    ## create empty file or edit timestamp of existing file
    def cmd_touch(self, args):
        try:
            with open(args[0], 'a'):
                os.utime(args[0], None) 
            print(f"File '{args[0]}' touched successfully.")
        except OSError as e:
            print(f"Error touching file: {e}")

    ## kill an existing job
    def cmd_kill(self, args):
        try:
            jid = int(args[0])
        except (IndexError, ValueError):
            print("kill: missing or invalid job ID")
            return

        for job in self.jobs:
            if job['id'] == jid:
                proc = job['proc']
                if proc.poll() is not None:
                    print(f"kill: job {jid} is already terminated")
                    return
                try:
                    try:
                        os.kill(proc.pid, signal.SIGTERM)
                    except Exception:
                        # Fallback for Windows
                        handle = win32api.OpenProcess(win32con.PROCESS_TERMINATE, False, proc.pid)
                        win32api.TerminateProcess(handle, -1)
                        win32api.CloseHandle(handle)

                    job['status'] = 'Killed'
                    print(f"Job [{jid}] (PID {proc.pid}) terminated.")
                    return
                except Exception as e:
                    print(f"kill: failed to terminate job {jid}: {e}")
                    return

        print(f"kill: job {jid} not found")

    ## List jobs
    def cmd_jobs(self, args):
        if not self.jobs:
            print("No jobs found")
        for job in self.jobs:
            print(f"[{job['id']}] | {job['status']} | {job['cmd']}")

    ## bring background job to the foreground
    def cmd_fg(self, args):
        jid = int(args[0])
        for job in list(self.jobs):
            if job['id'] == jid:
                proc = job['proc']
                try:
                    os.kill(proc.pid, signal.SIGCONT)
                except Exception:
                    pass
                print(f"Brining process to the foreground: {jid}")
                proc.wait()
                return
        print(f"fg: job {jid} not found")


    ## resume background job
    def cmd_bg(self, args):
        try:
            jid = int(args[0])
        except (IndexError, ValueError):
            print("bg: missing or invalid job id")
            return

        for job in self.jobs:
            if job['id'] == jid:
                proc = job['proc']
                if proc.poll() is None:
                    try:
                        handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, False, proc.pid)
                        NtResumeProcess(handle.handle)
                        win32api.CloseHandle(handle)
                        job['status'] = 'Running' ## Changing the status to running for resumed job
                        print(f"[{jid}] {proc.pid} resumed in background")
                    except Exception as e:
                        print(f"bg: failed to resume job [{jid}]: {e}")
                else:
                    print(f"bg: job [{jid}] is not running")
                return

        print(f"bg: job {jid} not found")


    ## Run a program in the bakcground
    def cmd_run(self, args):
        path = args[0]
        if not os.path.exists(path):
            print(f"run: file not found: {path}")
            return
        if path.endswith('.py'):
            cmd = [sys.executable, path] + args[1:]
        else:
            cmd = [path] + args[1:]
        try:
            proc = subprocess.Popen(cmd, preexec_fn=os.setpgrp if hasattr(os, 'setpgrp') else None)
            now = time.time()
            self.jobs.append({
                'id': self.next_job_id,
                'proc': proc,
                'cmd': ' '.join(cmd),
                'status':'Running',
                'create_time':    now,
                'first_scheduled': None,    
                'run_time':       0.0,       
                'completion_time': None
            })
            print(f"[{self.next_job_id}] {proc.pid}")
            self.next_job_id += 1
        except Exception as e:
            print(f"run: failed to execute {path}: {e}")

    ## Run with assigned priority
    def cmd_runp(self, args):
        if len(args) < 2:
            print("Usage: runp <priority> <path> [args...]")
            return

        try:
            prio = int(args[0])
        except ValueError:
            print("runp: priority must be an integer")
            return

        path, *rest = args[1:]
        cmd = [sys.executable, path] + rest if path.endswith('.py') else [path] + rest

        try:
            proc = subprocess.Popen(
                cmd,
                preexec_fn=os.setpgrp if hasattr(os, 'setpgrp') else None
            )
            now = time.time()
            self.jobs.append({
                'id':       self.next_job_id,
                'proc':     proc,
                'cmd':      ' '.join(cmd),
                'status':   'Running',
                'priority': prio,
                'create_time':    now,
                'first_scheduled': None,    
                'run_time':       0.0,       
                'completion_time': None
            })
            with self.jobs_lock:
                self.jobs.append(self.jobs)
                self.next_job_id += 1

            # hand off into the scheduler’s queue
            self.job_queue.put(self.jobs)

            print(f"[{self.jobs['id']}] {proc.pid} (priority {prio}) queued")
        except Exception as e:
            print(f"runp: failed to execute {' '.join(cmd)}: {e}")


    ## Pause a process running in the background
    def cmd_pause(self, args):
        try:
            jid = int(args[0])
        except (IndexError, ValueError):
            print("pause: missing or invalid job id")
            return

        for job in self.jobs:
            if job['id'] == jid:
                proc = job['proc']
                if proc.poll() is None:
                    try:
                        handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, False, proc.pid)
                        NtSuspendProcess(handle.handle)
                        win32api.CloseHandle(handle)
                        job['status'] = 'Paused' ## Setting status as paused
                        print(f"Job [{jid}] paused")
                    except Exception as e:
                        print(f"pause: failed to pause job [{jid}]: {e}")
                else:
                    print(f"pause: job [{jid}] is not running")
                return

        print(f"pause: job {jid} not found")

    def cmd_srr(self, args):
        try:
            q = float(args[0])
        except:
            print("Usage: srr <quantum>")
            return
        RoundRobinScheduler(self.jobs, q).run()

    def cmd_spri(self, args):
        scheduler = PriorityScheduler(self.jobs) ## creating the scheduler, will need to start it in a thread for dynamic scheduling
        t = threading.Thread(target=scheduler.run, daemon=True) ## Initialize the thread
        t.start() ## start the thread
        print("Priority scheduler started in background.")

    def cmd_meminit(self, args):
       # Usage: meminit <frames> <FIFO|LRU>
       if len(args)>=1:
           frames = int(args[0])
           algo = args[1] if len(args)>1 else 'FIFO'
           self.mm = MemoryManager(frames, algo)
           print(f"Memory manager initialized: {frames} frames, {algo}")
       else:
           print("Usage: meminit <frames> [FIFO|LRU]")

    def cmd_memadd(self, args):
       # Usage: memadd <pid>
        pid = int(args[0])
        with self.mm_lock:
            self.mm.add_process(pid)
        print(f"PID {pid} added")

    def cmd_memreq(self, args):
       # Usage: memreq <pid> <page>
       try:
           pid, page = map(int, args)
           hit = self.mm.access_page(pid, page)
           print(f"PID {pid} page {page} hit (in frame {self.mm.page_table[pid][page]})")
       except PageFault as pf:
           print(pf)
       except Exception as e:
           print(f"memreq error: {e}")

    def cmd_memstats(self, args):
       print(self.mm.stats())

    def cmd_pc_demo(self, args):
       buf = int(args[0]) if args else 5
       items = int(args[1]) if len(args)>1 else 20
       process_sync.producer_consumer(buf, items)

    def cmd_dp_demo(self, args):
       n = int(args[0]) if args else 5
       process_sync.dining_philosophers(n)

    def start_priority_service(self):
        """Start one background thread that will continuously consume jobs."""
        t = threading.Thread(target=self._priority_loop, daemon=True)
        t.start()

    def _priority_loop(self):
        from schedulers import suspend_process, resume_process  # or adjust imports
        import time, heapq

        active = []
        while True:
            # 1) If no active jobs, block waiting for at least one
            if not active:
                job = self.job_queue.get()
                active.append(job)
                self.job_queue.task_done()

            # 2) Build a heap of all currently alive jobs by priority
            active = [j for j in active if j['proc'].poll() is None]
            for _ in range(self.job_queue.qsize()):
                j = self.job_queue.get_nowait()
                active.append(j)
                self.job_queue.task_done()

            heap = [(-j['priority'], j) for j in active]
            heapq.heapify(heap)

            # 3) Pick highest‐priority job
            _, job = heapq.heappop(heap)
            active = [j for _, j in heap]  # remaining
            proc = job['proc']

            # 4) Run it until it finishes or a higher-priority job arrives
            resume_process(proc)
            while proc.poll() is None:
                try:
                    # non-blocking check for a new job
                    new = self.job_queue.get_nowait()
                    active.append(new)
                    self.job_queue.task_done()
                    # if new job outranks current, preempt
                    if new['priority'] > job['priority']:
                        suspend_process(proc)
                        active.append(job)
                        job = new
                        proc = job['proc']
                        resume_process(proc)
                except:
                    pass
                time.sleep(0.1)

            # it finished—loop around to pick the next one

if __name__ == '__main__':
    Shell().run()

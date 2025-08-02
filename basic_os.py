import os
import sys
import shlex
import signal
import subprocess
import time
import win32api
import win32con
import win32process
import win32event
import ctypes
from ctypes import wintypes

ntdll = ctypes.WinDLL("ntdll")

NtSuspendProcess = ntdll.NtSuspendProcess
NtSuspendProcess.restype = wintypes.ULONG
NtSuspendProcess.argtypes = [wintypes.HANDLE]

NtResumeProcess = ntdll.NtResumeProcess
NtResumeProcess.restype = wintypes.ULONG
NtResumeProcess.argtypes = [wintypes.HANDLE]

class Shell:
    def __init__(self):
        self.jobs = [] # initialiing job array to help with process management
        self.next_job_id = 1 # initializing first job id as 1 for first job    
        self.current_process = None # initializing current variable as null to track current process
        self.current_cmd = None # initializing current command variable as null to track current command

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
            'pause':self.cmd_pause
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
                os.utime(args[0], None)  # update timestamp or create if not exist
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
                    # Try POSIX-style termination
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
        for job in self.jobs:
            proc = job['proc']
            if proc.poll() is not None:
                job['status'] = 'Done'
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
                        NtResumeProcess(handle.handle)  # use .handle here too
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
        # Determine command
        if path.endswith('.py'):
            cmd = [sys.executable, path] + args[1:]
        else:
            cmd = [path] + args[1:]
        try:
            proc = subprocess.Popen(cmd, preexec_fn=os.setpgrp if hasattr(os, 'setpgrp') else None)
            self.jobs.append({
                'id': self.next_job_id,
                'proc': proc,
                'cmd': ' '.join(cmd),
                'status':'Running'
            })
            print(f"[{self.next_job_id}] {proc.pid}")
            self.next_job_id += 1
        except Exception as e:
            print(f"run: failed to execute {path}: {e}")


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
                        NtSuspendProcess(handle.handle)  # use .handle here
                        win32api.CloseHandle(handle)
                        job['status'] = 'Paused' ## Setting status as paused
                        print(f"Job [{jid}] paused")
                    except Exception as e:
                        print(f"pause: failed to pause job [{jid}]: {e}")
                else:
                    print(f"pause: job [{jid}] is not running")
                return

        print(f"pause: job {jid} not found")


        

if __name__ == '__main__':
    Shell().run()

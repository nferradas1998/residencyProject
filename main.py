#!/usr/bin/env python3
"""
Basic Python Shell with file system commands and job control.
"""
import os
import sys
import shlex
import signal
import subprocess
import time

class Shell:
    def __init__(self):
        self.jobs = []                # background jobs list
        self.next_job_id = 1          # incremental job IDs
        self.current_process = None   # foreground process
        self.current_cmd = None       # last launched command string

        # Map built-in commands to handler methods
        self.builtins = {
            'cd':     self.cmd_cd,
            'pwd':    self.cmd_pwd,
            'exit':   self.cmd_exit,
            'echo':   self.cmd_echo,
            'clear':  self.cmd_clear,
            'ls':     self.cmd_ls,
            'cat':    self.cmd_cat,
            'mkdir':  self.cmd_mkdir,
            'rmdir':  self.cmd_rmdir,
            'rm':     self.cmd_rm,
            'touch':  self.cmd_touch,
            'kill':   self.cmd_kill,
            'jobs':   self.cmd_jobs,
            'fg':     self.cmd_fg,
            'bg':     self.cmd_bg,
        }

        # Handle Ctrl-Z to stop foreground jobs
        signal.signal(signal.SIGTSTP, self.handle_sigtstp)
        # Ignore Ctrl-C in shell
        signal.signal(signal.SIGINT, lambda s, f: print())

    def handle_sigtstp(self, signum, frame):
        # implement here
        print()

    def run(self):
        print("BasicOS Shell. Type 'help' for commands.")
        while True:
            try:
                line = input('> ').strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not line:
                continue

            # background execution if trailing '&'
            background = line.endswith('&')
            if background:
                line = line[:-1].strip()

            parts = shlex.split(line)
            cmd = parts[0]
            args = parts[1:]

            # built-in commands
            if cmd in self.builtins:
                self.builtins[cmd](args)
            else:
                self.launch_cmd(parts, background)

    def launch_cmd(self, parts, background):
        # Launch external command
        proc = subprocess.Popen(parts, preexec_fn=os.setpgrp)
        self.current_process = proc
        self.current_cmd = ' '.join(parts)

        if background:
            self.jobs.append({
                'id': self.next_job_id,
                'proc': proc,
                'cmd': self.current_cmd,
            })
            print(f"[{self.next_job_id}] {proc.pid}")
            self.next_job_id += 1
            self.current_process = None
        else:
            proc.wait()
            self.current_process = None

    # Built-in handlers
    def cmd_cd(self, args):
        # implement here
        print()

    def cmd_pwd(self, args):
        # implement here
        print()

    def cmd_exit(self, args):
        # implement here
        print()

    def cmd_echo(self, args):
        # implement here
        print()

    def cmd_clear(self, args):
        # implement here
        if sys.platform.startswith('win'):
            os.system('cls')
        else:
            os.system('clear')
        print(f"Terminal cleared")

    def cmd_ls(self, args):
        # implement here
        curr_dir = "."
        files = []
        entries = os.listdir(curr_dir)
        for entry in entries:
            full_path = os.path.join(curr_dir, entry)
            if os.path.isfile(full_path):
                files.append(entry)

        for filename in files:
            print(filename)

    def cmd_cat(self, args):
        # implement here
        try:
            with open(args[0], 'r') as f:
                content = f.read()
                print(content)
        except FileNotFoundError:
            print(f"File Not Found")
        except Exception as e:
            print(f"An error occurred: {e}")

    def cmd_mkdir(self, args):
        try:
            os.mkdir(args[0])
            print(f"Directory '{args[0]}' created successfully.")
        except FileExistsError:
            print(f"Directory '{args[0]}' already exists.")
        except OSError as e:
            print(f"Error creating directory: {e}")

    def cmd_rmdir(self, args):
        if not args:
            print("Usage: rmdir [directory]")
            return
        try:
            os.rmdir(args[0])
            print(f"Directory '{args[0]}' removed successfully.")
        except FileNotFoundError:
            print(f"Directory '{args[0]}' not found.")
        except OSError as e:
            print(f"Error removing directory: {e}")

    def cmd_rm(self, args):
        if not args:
            print("Usage: rm [filename]")
            return
        try:
            os.remove(args[0])
            print(f"File '{args[0]}' removed successfully.")
        except FileNotFoundError:
            print(f"File '{args[0]}' not found.")
        except IsADirectoryError:
            print(f"'{args[0]}' is a directory. Use rmdir to remove directories.")
        except OSError as e:
            print(f"Error removing file: {e}")

    def cmd_touch(self, args):
        if not args:
            print("Usage: touch [filename]")
            return
        try:
            with open(args[0], 'a'):
                os.utime(args[0], None)  # update timestamp or create if not exist
            print(f"File '{args[0]}' touched successfully.")
        except OSError as e:
            print(f"Error touching file: {e}")

    def cmd_kill(self, args):
        if not args:
            print("Usage: kill [pid]")
            return
        try:
            pid = int(args[0])
            os.kill(pid, signal.SIGTERM)
            print(f"Process {pid} terminated.")
        except ProcessLookupError:
            print(f"No process found with PID {pid}.")
        except ValueError:
            print("Invalid PID.")
        except PermissionError:
            print(f"Permission denied to terminate process {pid}.")
        except OSError as e:
            print(f"Error killing process {pid}: {e}")

    def cmd_jobs(self, args):
        # implement here
        print()

    def cmd_fg(self, args):
        # implement here
        print()

    def cmd_bg(self, args):
        # implement here
        print()

if __name__ == '__main__':
    Shell().run()

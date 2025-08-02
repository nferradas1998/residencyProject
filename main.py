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
        print()

    def cmd_ls(self, args):
        # implement here
        print()

    def cmd_cat(self, args):
        # implement here
        print()

    def cmd_mkdir(self, args):
        # implement here
        print()

    def cmd_rmdir(self, args):
        for filename in args:
            try:
                os.remove(filename)
            except Exception as e:
                print(f"rm: {e}")


    def cmd_rm(self, args):
     for filename in args:
            try:
                os.remove(filename)
            except Exception as e:
                print(f"rm: {e}")

    def cmd_touch(self, args):
     for filename in args:
            try:
                with open(filename, 'a'):
                    os.utime(filename, None)
            except Exception as e:
                print(f"touch: {e}")

    def cmd_kill(self, args):
       for filename in args:
            try:
                with open(filename, 'a'):
                    os.utime(filename, None)
            except Exception as e:
                print(f"touch: {e}")

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

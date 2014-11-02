#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""keepuppy_restart
"""

from __future__ import print_function
import sys
import os
import psutil
import signal
from time import sleep
import subprocess


DEFAULT_PROCESS_NAME = 'KeePassX'
DEFAULT_TIMEOUT = 30
DEFAULT_START_COMMAND = "open -a '%s'" % DEFAULT_PROCESS_NAME


class OptionError(Exception):
    """An option error has occurred."""


class ScriptError(Exception):
    """A script error has occurred."""


class Options(object):

    option_lookup = {
        'process_name': ('KEEPUPPY_RESTART_PROCESS_NAME', DEFAULT_PROCESS_NAME, False),
        'timeout': ('KEEPUPPY_RESTART_TIMEOUT', DEFAULT_TIMEOUT, False),
        'start_command': ('KEEPUPPY_RESTART_START_COMMAND', DEFAULT_START_COMMAND, False),
    }

    @classmethod
    def __getattr__(cls, item):
        if item in cls.option_lookup:
            env, val, required = cls.option_lookup[item]
            if env in os.environ:
                val = os.environ[env]

            if required and val is None:
                raise OptionError("Environment variable '%s' is required" % env)

            return val

        raise OptionError("Unknown option '%s'" % item)


def find_pid_of_process(name):
    pid_list = psutil.pids()
    for pid in pid_list:
        try:
            proc = psutil.Process(pid)
            if proc.name() == name:
                return pid

        except psutil.NoSuchProcess:
            pass

    return None


def process_running(pid):
    try:
        proc = psutil.Process(pid)

    except psutil.NoSuchProcess:
        return False

    return True


def do_restart(options):
    pid = find_pid_of_process(options.process_name)
    print("Stopping process name (%s) pid (%s)" % (options.process_name, pid))
    os.kill(pid, signal.SIGTERM)

    print('Waiting for process to stop')
    stopped = False
    while range(options.timeout):
        if not process_running(pid):
            stopped = True
            break

        sleep(1)

    if stopped:
        print("Starting process with command (%s)" % options.start_command)
        try:
            output = subprocess.check_output(options.start_command,
                                             stderr = subprocess.STDOUT,
                                             shell = True)
            if output:
                print('Command output\n----\n%s\n----' % output)

        except subprocess.CalledProcessError as ex:
            msg = 'Command failed (%s)' % ex
            if ex.output:
                msg += '\n----\n%s\n----' % ex.output

            print(msg)

    else:
        raise ScriptError("Failed to stop process name (%s) pid (%s)" % (options.process_name, pid))

    return None


def keepuppy_restart():
    options = Options()
    do_restart(options)


if __name__ == "__main__":
    try:
        keepuppy_restart()

    except (OptionError, ScriptError) as e:
        print('Error:', e, file = sys.stderr)
        sys.exit(1)

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""keepuppy_sync
"""

from __future__ import print_function
import sys
import keepuppy
import logging
import os
import psutil
import signal
from time import sleep
import shlex
import subprocess


DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_STREAM = sys.stderr
DEFAULT_CACHE_FILE = '~/.keepuppy_cache.json'
DEFAULT_HOST_NAME = 'localhost'
DEFAULT_HOST_PORT = 22
DEFAULT_RESTART_APP = 'KeePassX'
DEFAULT_RESTART_TIMEOUT = 30


class OptionError(Exception):
    """An option error has occurred."""


class Options(object):

    option_lookup = {
        'cache_file': ('KEEPUPPY_CACHE_FILE', DEFAULT_CACHE_FILE, True),
        'local_file': ('KEEPUPPY_LOCAL_FILE', None, True),
        'remote_file': ('KEEPUPPY_REMOTE_FILE', None, True),
        'restart_app': ('KEEPUPPY_RESTART_APP', DEFAULT_RESTART_APP, False),
        'restart_timeout': ('KEEPUPPY_RESTART_TIMEOUT', DEFAULT_RESTART_TIMEOUT, False),
        'remote_user_name': ('KEEPUPPY_SFTP_USER_NAME', None, False),
        'remote_password': ('KEEPUPPY_SFTP_PASSWORD', None, False),
        'remote_host_name': ('KEEPUPPY_SFTP_HOST_NAME', DEFAULT_HOST_NAME, True),
        'remote_host_port': ('KEEPUPPY_SFTP_HOST_PORT', DEFAULT_HOST_PORT, True),
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


def enable_logging(log_level = DEFAULT_LOG_LEVEL, log_stream = DEFAULT_LOG_STREAM):
    log = logging.getLogger("keepuppy")
    log.setLevel(log_level)
    log_handler = logging.StreamHandler(log_stream)
    log_format = logging.Formatter("%(name)s [%(levelname)s]: %(message)s")
    log_handler.setFormatter(log_format)
    log_handler.setLevel(log_level)
    log.addHandler(log_handler)


def restart_app(options):

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

    def restart_app_func(file_object):
        if options.restart_app:
            pid = find_pid_of_process(options.restart_app)
            os.kill(pid, signal.SIGTERM)

        pid = None
        while range(options.restart_timeout):
            pid = find_pid_of_process(options.restart_app)

            if pid is None:
                break

            sleep(1)

        if pid is None:
            cmd = "open -a '%s'" % options.restart_app
            subprocess.call(shlex.split(cmd))

        return None

    return restart_app_func


def do_sync(options):
    file_local = keepuppy.FileLocal(options.local_file)

    file_remote = keepuppy.FileSFTP(options.remote_file,
                                    options.remote_user_name,
                                    options.remote_password,
                                    options.remote_host_name,
                                    options.remote_host_port)

    hash_cache = keepuppy.HashCache(options.cache_file)
    syncer = keepuppy.Syncer(hash_cache, restart_app(options))
    status = syncer.sync(file_local, file_remote)
    if status is not None:
        print(status)


def run_keepuppy():
    enable_logging()
    options = Options()
    do_sync(options)

if __name__ == "__main__":
    try:
        run_keepuppy()

    except (OptionError, keepuppy.FileException, keepuppy.HashCacheException, keepuppy.SyncException) as e:
        print('Error:', e, file = sys.stderr)
        sys.exit(1)

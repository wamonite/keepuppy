#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""keepuppy_sync
"""

from __future__ import print_function
import sys
import keepuppy
import logging
import os
import subprocess


DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_STREAM = sys.stderr
DEFAULT_CACHE_FILE = '~/.keepuppy_cache.json'
DEFAULT_HOST_NAME = 'localhost'
DEFAULT_HOST_PORT = 22


class OptionError(Exception):
    """An option error has occurred."""


class Options(object):

    option_lookup = {
        'cache_file': ('KEEPUPPY_CACHE_FILE', DEFAULT_CACHE_FILE, True),
        'local_file': ('KEEPUPPY_LOCAL_FILE', None, True),
        'remote_file': ('KEEPUPPY_REMOTE_FILE', None, True),
        'restart_command': ('KEEPUPPY_RESTART_COMMAND', None, False),
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


def restart_command(options):

    def restart_command_func(file_object):
        if options.restart_command:
            try:
                cmd = options.restart_command
                cmd = cmd.replace('[file_name]', file_object.name)
                print('Calling restart command (%s)' % cmd)

                output = subprocess.check_output(cmd,
                                                 stderr = subprocess.STDOUT,
                                                 shell = True)
                if output:
                    print('Restart command output\n----\n%s\n----' % output)

            except subprocess.CalledProcessError as ex:
                msg = 'Restart command failed (%s)' % ex
                if ex.output:
                    msg += '\n----\n%s\n----' % ex.output

                print(msg)

    return restart_command_func


def do_sync(options):
    file_local = keepuppy.FileLocal(options.local_file)

    file_remote = keepuppy.FileSFTP(options.remote_file,
                                    options.remote_user_name,
                                    options.remote_password,
                                    options.remote_host_name,
                                    options.remote_host_port)

    hash_cache = keepuppy.HashCache(options.cache_file)
    syncer = keepuppy.Syncer(hash_cache, restart_command(options))
    status = syncer.sync(file_local, file_remote)
    if status is not None:
        print(status)


def keepuppy_sync():
    enable_logging()
    options = Options()
    do_sync(options)

if __name__ == "__main__":
    try:
        keepuppy_sync()

    except (OptionError, keepuppy.FileException, keepuppy.HashCacheException, keepuppy.SyncException) as e:
        print('Error:', e, file = sys.stderr)
        sys.exit(1)

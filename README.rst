Keepuppy
========

.. default-role:: literal


.. image:: http://img.shields.io/github/tag/wamonite/keepuppy.svg
    :target: https://github.com/wamonite/keepuppy

.. image:: https://travis-ci.org/wamonite/keepuppy.svg?branch=master
    :target: https://travis-ci.org/wamonite/keepuppy

.. image:: https://requires.io/github/wamonite/keepuppy/requirements.svg?branch=master
    :target: https://requires.io/github/wamonite/keepuppy/requirements/?branch=master

Keepuppy is a Python package and associated scripts to keep a Keepass database file in sync between the local filesystem of multiple clients and an SFTP server. Optionally a command can be executed if the local file is updated. An example script is provided to restart KeePassX.

Scripts
-------

`keepuppy_sync.py` is a script to perform the file synchronisation. `keepuppy_restart.py` is a script to restart an application, KeePassX by default, which can be called by `keepuppy_sync.py` when the local file is updated.

Configuration values are set via environment variables. I recommend using a tool such as envdir_.

::

    keepuppy_sync.py

- KEEPUPPY_CACHE_FILE: File to store file hashes (default '~/.keepuppy_cache.json')
- KEEPUPPY_LOCAL_FILE: Path to the local file (required)
- KEEPUPPY_REMOTE_FILE: Path on the SFTP server to the file (required)
- KEEPUPPY_RESTART_COMMAND: Script or shell command to execute when the local file is updated
- KEEPUPPY_SFTP_USER_NAME: SFTP user name
- KEEPUPPY_SFTP_PASSWORD: SFTP password
- KEEPUPPY_SFTP_HOST_NAME: SFTP server name (default 'localhost')
- KEEPUPPY_SFTP_HOST_PORT: SFTP server port (default '22')

If the KEEPUPPY_RESTART_COMMAND value contains `[file_name]` it with be replaced with the name of the updated local file.

::

    keepuppy_restart.py

- KEEPUPPY_RESTART_PROCESS_NAME: name of the process to restart (default 'KeePassX')
- KEEPUPPY_RESTART_TIMEOUT: time in seconds to wait for the process to stop (default '30')
- KEEPUPPY_RESTART_START_COMMAND: script or shell command to execute to start the new process (default 'open -a "KeePassX"')

.. Note:: To work with KeePassX, and not lose data when restarted by script, check *Preferences -> General (2) -> Automatically save database after every change*.

License
-------

Copyright (c) 2014 Warren Moore

This software may be redistributed under the terms of the MIT License.
See the file LICENSE for details.

Contact
-------

::

          @wamonite     - twitter
           \_______.com - web
    warren____________/ - email

.. _envdir: http://envdir.readthedocs.org/en/latest/

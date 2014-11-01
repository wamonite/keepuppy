# -*- coding: utf-8 -*-

from .exceptions import FileException, HashCacheException, SyncException
import json
from hashlib import md5
from datetime import datetime
import os
import logging

log = logging.getLogger(__name__)


class HashCache(object):

    def __init__(self, cache_file_name):
        self.cache_file_name = os.path.expanduser(cache_file_name)
        self.cache = {}

        self._load_hashes()

    def get_hash(self, file_object):
        with file_object:
            last_changed = file_object.last_changed()
            log.debug('File key (%s) last_changed (%s)' % (file_object.key, last_changed))

            if last_changed:
                return self._read_or_calculate_hash(file_object, file_object.key, last_changed)

        return None

    def _read_or_calculate_hash(self, file_object, key, last_changed):
        file_info = self.cache.setdefault(key, {})
        last_changed_cached = file_info.get('last_changed')
        file_hash_cached = file_info.get('file_hash')

        last_changed_str = last_changed.strftime('%Y-%m-%d %H:%M:%S')

        created = not file_info
        calculate_hash = last_changed_cached != last_changed_str
        if calculate_hash:
            file_hash = self.calculate_hash(file_object.read())
            file_info['last_changed'] = last_changed_str
            file_info['file_hash'] = file_hash

            self._save_hashes()

        return {
            'last_changed': datetime.strptime(file_info['last_changed'], '%Y-%m-%d %H:%M:%S'),
            'file_hash': file_info['file_hash'],
            'file_hash_previous': file_hash_cached,
            'created': created,
            'calculated': calculate_hash,
            'updated': not created and calculate_hash and file_hash_cached != file_info['file_hash']
        }

    @staticmethod
    def calculate_hash(data):
        m = md5()
        m.update(data)
        return m.hexdigest()

    def _load_hashes(self):
        try:
            with open(self.cache_file_name, 'rb') as file_object:
                self.cache = json.load(file_object)

        except ValueError:
            raise HashCacheException('Cache file exists but does not contain valid data')

        except IOError as e:
            log.warning('Unable to load hash cache file (%s) (%s)' % (self.cache_file_name, e))

    def _save_hashes(self):
        with open(self.cache_file_name, 'wb') as file_object:
            json.dump(self.cache, file_object)


class Syncer(object):

    conflict_suffix = '_conflict'
    _hash_cache = None
    _func_local_update = None

    def __init__(self, hash_cache, func_local_update = None):
        self._hash_cache = hash_cache
        self._func_local_update = func_local_update

    @property
    def hash_cache(self):
        return self._hash_cache

    def sync(self, file_local, file_remote):
        try:
            info_local = self._hash_cache.get_hash(file_local) if file_local else None

        except (FileException, HashCacheException) as e:
            raise SyncException('Local file error', e)

        try:
            info_remote = self._hash_cache.get_hash(file_remote) if file_remote else None

        except (FileException, HashCacheException) as e:
            raise SyncException('Remote file error', e)

        log.debug('File info local (%s)' % info_local)
        log.debug('File info remote (%s)' % info_remote)

        if not info_local and not info_remote:
            raise SyncException('No files found locally or remotely')

        elif not info_local:
            self._copy_file(file_remote, file_local)

            if self._func_local_update:
                self._func_local_update(file_local)

            return 'Local file missing, copying remote'

        elif not info_remote:
            self._copy_file(file_local, file_remote)

            return 'Remote file missing, copying local'

        if info_local.get('file_hash') == info_remote.get('file_hash'):
            return 'Files are up to date'

        file_new_local = info_local.get('created') or info_local.get('updated')
        file_new_remote = info_remote.get('created') or info_remote.get('updated')
        if file_new_local and file_new_remote:
            log.warning('Local and remote files have both been modified so creating backup')
            self._create_backup(file_local, conflict = True)

        if info_local.get('last_changed') > info_remote.get('last_changed'):
            self._copy_file(file_local, file_remote)

            return 'Local file most recent, copying remotely'

        else:
            self._copy_file(file_remote, file_local)

            return 'Remote file most recent, copying locally'

    def _copy_file(self, file_source, file_destination):
        try:
            file_data = file_source.read()
            file_destination.write(file_data)

            self._hash_cache.get_hash(file_destination)

        except FileException as e:
            raise SyncException('Failed to copy file', e)

    def _create_backup(self, file_object, conflict = False):
        try:
            time_now = datetime.utcnow()
            file_name = file_object.name + '.' + time_now.strftime('%Y%m%d_%H%M%S')
            if conflict:
                file_name += self.conflict_suffix
            log.info('Creating backup (%s)' % file_name)

            file_object.copy(file_name)

        except (FileException, IOError) as e:
            raise SyncException('Failed to create file backup', e)

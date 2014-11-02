# -*- coding: utf-8 -*-

from keepuppy.sync import Syncer, HashCache
from keepuppy.exceptions import FileException, HashCacheException, SyncException
import os
import tempfile
from nose.tools import eq_, assert_true, raises, assert_raises
from datetime import datetime, timedelta
import json
from mock import MagicMock
from collections import namedtuple
import logging

log = logging.getLogger(__name__)


class FileMockGenerator(object):

    name_index = 0

    def get(self):
        mock_file = MagicMock()

        file_name = 'mock%05d' % self.name_index
        self.name_index += 1

        mock_file.name = file_name
        mock_file.key = 'mock|%s' % file_name

        self.set_time(mock_file, datetime.utcnow())
        self.set_data(mock_file, HashCache.calculate_hash(file_name))

        return mock_file

    @staticmethod
    def format_time(file_time):
        return file_time - timedelta(microseconds = file_time.microsecond)

    @staticmethod
    def set_time(file_object, file_time):
        file_object.last_changed.return_value = FileMockGenerator.format_time(file_time)

    @staticmethod
    def offset_time(file_object, time_offset):
        file_time = file_object.last_changed() + time_offset
        file_object.last_changed.return_value = FileMockGenerator.format_time(file_time)

    @staticmethod
    def set_data(file_object, file_data):
        file_object.read.return_value = file_data


class TestHashCache(object):

    file_cache = None
    file_mock_generator = None

    def setup(self):
        self.file_cache = tempfile.NamedTemporaryFile(delete = False)
        self.delete_file(self.file_cache.name)
        log.debug('File cache (%s)' % self.file_cache.name)

        self.file_mock_generator = FileMockGenerator()

    def teardown(self):
        self.delete_file(self.file_cache.name)

    @staticmethod
    def delete_file(file_name):
        try:
            os.unlink(file_name)

        except OSError:
            pass

    @staticmethod
    def calculate_cache_data(file_object_list):
        cache_data = {}
        for file_object in file_object_list:
            file_time = file_object.last_changed()
            file_time_str = file_time.strftime('%Y-%m-%d %H:%M:%S')

            cache_key = file_object.key
            cache_data[cache_key] = {
                'last_changed': file_time_str,
                'file_hash': HashCache.calculate_hash(file_object.read())
            }

        return cache_data

    def write_cache_data(self, file_object_list):
        cache_data = self.calculate_cache_data(file_object_list)

        with open(self.file_cache.name, 'wb') as cache_file:
            json.dump(cache_data, cache_file)

    def compare_cache_data(self, file_object_list):
        cache_data_calculated = self.calculate_cache_data(file_object_list)
        cache_data_saved = {}
        try:
            with open(self.file_cache.name) as file_object:
                cache_data_saved = json.load(file_object)

        except IOError:
            pass

        eq_(cache_data_calculated, cache_data_saved)

    @staticmethod
    def check_cache_result(cache_data, file_object, created, calculated, updated):
        assert_true(cache_data is not None)
        eq_(cache_data.get('last_changed'), file_object.last_changed())
        eq_(cache_data.get('file_hash'), HashCache.calculate_hash(file_object.read()))
        eq_(cache_data.get('created'), created)
        eq_(cache_data.get('calculated'), calculated)
        eq_(cache_data.get('updated'), updated)

    def test_cache_created(self):
        mock_file = self.file_mock_generator.get()

        hash_cache = HashCache(self.file_cache.name)

        cache_data = hash_cache.get_hash(mock_file)

        self.check_cache_result(cache_data,
                                mock_file,
                                True,
                                True,
                                False)

        self.compare_cache_data([mock_file])

    def test_cache_read(self):
        mock_file = self.file_mock_generator.get()
        self.write_cache_data([mock_file])

        hash_cache = HashCache(self.file_cache.name)

        cache_data = hash_cache.get_hash(mock_file)

        self.check_cache_result(cache_data,
                                mock_file,
                                False,
                                False,
                                False)

        self.compare_cache_data([mock_file])

    def test_cache_calculated(self):
        mock_file = self.file_mock_generator.get()
        self.write_cache_data([mock_file])

        hash_cache = HashCache(self.file_cache.name)

        FileMockGenerator.offset_time(mock_file, timedelta(hours = 1))

        cache_data = hash_cache.get_hash(mock_file)

        self.check_cache_result(cache_data,
                                mock_file,
                                False,
                                True,
                                False)

        self.compare_cache_data([mock_file])

    def test_cache_updated(self):
        mock_file = self.file_mock_generator.get()
        self.write_cache_data([mock_file])

        hash_cache = HashCache(self.file_cache.name)

        FileMockGenerator.offset_time(mock_file, timedelta(hours = 1))
        FileMockGenerator.set_data(mock_file, mock_file.read()[::-1])

        cache_data = hash_cache.get_hash(mock_file)

        self.check_cache_result(cache_data,
                                mock_file,
                                False,
                                True,
                                True)

        self.compare_cache_data([mock_file])

    def test_cache_multiple(self):
        mock_file_list = [self.file_mock_generator.get(), self.file_mock_generator.get()]

        hash_cache = HashCache(self.file_cache.name)

        cache_data_list = [hash_cache.get_hash(mock_file) for mock_file in mock_file_list]

        for cache_data, mock_file in zip(cache_data_list, mock_file_list):
            self.check_cache_result(cache_data,
                                    mock_file,
                                    True,
                                    True,
                                    False)

        self.compare_cache_data(mock_file_list)

    @raises(FileException)
    def test_exception_on_last_changed(self):
        mock_file = self.file_mock_generator.get()
        mock_file.last_changed.side_effect = FileException('')

        hash_cache = HashCache(self.file_cache.name)

        hash_cache.get_hash(mock_file)

    @raises(FileException)
    def test_exception_on_read(self):
        mock_file = self.file_mock_generator.get()
        mock_file.read.side_effect = FileException('')

        hash_cache = HashCache(self.file_cache.name)

        hash_cache.get_hash(mock_file)

    @raises(IOError)
    def test_exception_on_save(self):
        mock_file = self.file_mock_generator.get()

        hash_cache = HashCache(self.file_cache.name + 'path/ensures/write/will/fail')

        hash_cache.get_hash(mock_file)

    @raises(HashCacheException)
    def test_exception_invalid_data(self):
        with open(self.file_cache.name, 'wb') as file_object:
            file_object.write('stuff')

        mock_file = self.file_mock_generator.get()

        hash_cache = HashCache(self.file_cache.name)

        hash_cache.get_hash(mock_file)


class TestSyncLogic(object):

    hash_lookup = {}
    syncer = None
    local = 'local'
    remote = 'remote'

    def hash_cache_lookup(self, file_key):
        return self.hash_lookup.get(file_key)

    def setup(self):
        hash_cache = MagicMock()
        hash_cache.get_hash.side_effect = self.hash_cache_lookup

        self.syncer = Syncer(hash_cache)
        self.syncer._copy_file = MagicMock()
        self.syncer._create_backup = MagicMock()
        self.syncer._local_update = MagicMock()

        self.hash_lookup = {}

    def teardown(self):
        pass

    @staticmethod
    def generate_hash_result(*args):
        arg_names = ['last_changed', 'file_hash', 'created', 'updated']
        return dict(zip(arg_names, args))

    def check_calls(self, copy_file_args, backup_args, update_func):
        if copy_file_args:
            eq_(len(self.syncer._copy_file.call_args_list), 1)
            eq_(self.syncer._copy_file.call_args_list[0][0], copy_file_args)

        else:
            eq_(len(self.syncer._copy_file.call_args_list), 0)

        if backup_args:
            eq_(len(self.syncer._create_backup.call_args_list), 1)
            eq_(self.syncer._create_backup.call_args_list[0][0], backup_args)

        else:
            eq_(len(self.syncer._create_backup.call_args_list), 0)

        eq_(len(self.syncer._local_update.call_args_list) == 1, update_func)

    TestParams = namedtuple('TestParams', ['exception_thrown',
                                           'local_exists', 'local_hash', 'local_created', 'local_updated',
                                           'remote_exists', 'remote_hash', 'remote_created', 'remote_updated',
                                           'time_offset',
                                           'copy_file_args', 'backup_args', 'update_func'])

    def check_logic(self, test_params):
        tp = test_params

        local_time = datetime.utcnow()

        if tp.local_exists:
            self.hash_lookup[self.local] = self.generate_hash_result(local_time,
                                                                     tp.local_hash,
                                                                     tp.local_created,
                                                                     tp.local_updated)

        if tp.remote_exists:
            remote_time = local_time + timedelta(hours = tp.time_offset) if tp.time_offset != 0 else local_time

            self.hash_lookup[self.remote] = self.generate_hash_result(remote_time,
                                                                      tp.remote_hash,
                                                                      tp.remote_created,
                                                                      tp.remote_updated)

        if not tp.exception_thrown:
            self.syncer.sync(self.local, self.remote)

        else:
            assert_raises(tp.exception_thrown, self.syncer.sync, self.local, self.remote)

        self.check_calls(tp.copy_file_args, tp.backup_args, tp.update_func)

    def test_logic(self):
        copy_from_remote = (self.remote, self.local)
        copy_to_remote = (self.local, self.remote)
        backup = (self.local,)
        conflict = (self.local, True)
        check_logic_arg_list = [
            (SyncException, False, '', False, False, False, '', False, False, 0, None, None, False),
            (None, True, 'abcd', False, False, False, '', False, False, 0, copy_to_remote, None, False),
            (None, False, '', False, False, True, 'abcd', False, False, 0, copy_from_remote, None, True),
            (None, True, 'abcd', False, False, True, 'abcd', False, False, 0, None, None, False),

            (None, True, 'abcd', False, False, True, 'efgh', False, False, 1, copy_from_remote, backup, True),
            (None, True, 'abcd', True, False, True, 'efgh', True, False, 1, copy_from_remote, conflict, True),
            (None, True, 'abcd', False, True, True, 'efgh', True, False, 1, copy_from_remote, conflict, True),
            (None, True, 'abcd', True, False, True, 'efgh', False, True, 1, copy_from_remote, conflict, True),
            (None, True, 'abcd', False, True, True, 'efgh', False, True, 1, copy_from_remote, conflict, True),

            (None, True, 'abcd', False, False, True, 'efgh', False, False, -1, copy_to_remote, None, False),
            (None, True, 'abcd', True, False, True, 'efgh', True, False, -1, copy_to_remote, conflict, False),
            (None, True, 'abcd', False, True, True, 'efgh', True, False, -1, copy_to_remote, conflict, False),
            (None, True, 'abcd', True, False, True, 'efgh', False, True, -1, copy_to_remote, conflict, False),
            (None, True, 'abcd', False, True, True, 'efgh', False, True, -1, copy_to_remote, conflict, False),
        ]

        for check_logic_args in check_logic_arg_list:
            yield self.check_logic, self.TestParams(*check_logic_args)

# -*- coding: utf-8 -*-

from keepuppy.files import FileLocal, FileSFTP
from keepuppy.exceptions import FileException
import os
import tempfile
from nose.tools import eq_, assert_true, assert_false, raises
from datetime import datetime
from sftp_server import SFTPAuth, SFTPServer
import logging

log = logging.getLogger(__name__)


@raises(FileException)
def test_local_no_file_name():
    FileLocal(None)


@raises(FileException)
def test_sftp_no_file_name():
    FileSFTP(None, None, None, None, None)


class TestFileBase(object):

    file_name = 'test.txt'
    file_data = '012345'
    rename_suffix = '.rename'

    file_object = None


class TestFileLocalMissing(TestFileBase):

    file_name = '/this/file/does/not/exist/and/path/ensures/write/will/fail'

    def setup(self):
        self.file_object = FileLocal(self.file_name)

    def test_open(self):
        assert_false(self.file_object.exists())

    def test_open_with(self):
        with self.file_object as f:
            assert_false(f.exists())

    def test_changed(self):
        assert_true(self.file_object.last_changed() is None)

    def test_changed_with(self):
        with self.file_object as f:
            assert_true(f.last_changed() is None)

    def test_key(self):
        assert_true(isinstance(self.file_object.key, str))

    @raises(FileException)
    def test_read(self):
        self.file_object.read()

    @raises(FileException)
    def test_read_with(self):
        with self.file_object as f:
            f.read()

    @raises(FileException)
    def test_write(self):
        self.file_object.write(self.file_data)

    @raises(FileException)
    def test_write_with(self):
        with self.file_object as f:
            f.write(self.file_data)

    @raises(FileException)
    def test_rename(self):
        new_file_name = self.file_object.name + self.rename_suffix
        self.file_object.rename(new_file_name)

    @raises(FileException)
    def test_rename_with(self):
        new_file_name = self.file_object.name + self.rename_suffix
        with self.file_object as f:
            f.rename(new_file_name)


class TestFileLocal(TestFileBase):

    temp_file = None

    def setup(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete = False)
        self.temp_file.write(self.file_data)
        self.temp_file.close()

        self.file_object = FileLocal(self.temp_file.name)

    def teardown(self):
        self.delete_file_data()

    def read_file_data(self):
        with open(self.temp_file.name) as f:
            return f.read()

    def delete_file_data(self):
        for file_name in [self.temp_file.name, self.temp_file.name + self.rename_suffix]:
            try:
                os.unlink(file_name)

            except OSError:
                pass

    def test_type(self):
        eq_(self.file_object.source_type, 'local')

    def test_open(self):
        assert_true(self.file_object.exists())

    def test_open_with(self):
        with self.file_object as f:
            assert_true(f.exists())

    def test_changed(self):
        assert_true(isinstance(self.file_object.last_changed(), datetime))

    def test_changed_with(self):
        with self.file_object as f:
            assert_true(isinstance(f.last_changed(), datetime))

    def test_key(self):
        assert_true(isinstance(self.file_object.key, str))

    def test_read(self):
        eq_(self.file_object.read(), self.file_data)

    def test_read_with(self):
        with self.file_object as f:
            eq_(f.read(), self.file_data)

    def test_write(self):
        self.file_object.write(self.file_data)

        eq_(self.read_file_data(), self.file_data)

    def test_write_with(self):
        with self.file_object as f:
            eq_(f.read(), self.file_data)

        eq_(self.read_file_data(), self.file_data)

    def test_rename(self):
        new_file_name = self.file_object.name + self.rename_suffix
        self.file_object.rename(new_file_name)

        eq_(self.file_object.name, new_file_name)
        assert_true(self.file_object.exists())

    def test_rename_with(self):
        new_file_name = self.file_object.name + self.rename_suffix
        with self.file_object as f:
            f.rename(new_file_name)

        eq_(self.file_object.name, new_file_name)
        assert_true(self.file_object.exists())

    def test_copy(self):
        file_name = self.file_object.name + '.copy'
        copy_object = self.file_object.copy(file_name)

        assert_true(self.file_object.name != copy_object.name)
        eq_(copy_object.read(), self.file_data)

    def test_copy_with(self):
        with self.file_object as f:
            file_name = f.name + '.copy'
            copy_object = f.copy(file_name)

        assert_true(self.file_object.name != copy_object.name)
        eq_(copy_object.read(), self.file_data)


class TestFileSFTPUnconnected(TestFileBase):

    def setup(self):
        self.file_object = FileSFTP(self.file_name,
                                    SFTPAuth.user_name,
                                    SFTPAuth.password,
                                    SFTPServer.host_name,
                                    SFTPServer.host_port)

    def teardown(self):
        self.file_object.close()

    def test_type(self):
        eq_(self.file_object.source_type, 'SFTP')

    @raises(FileException)
    def test_open(self):
        self.file_object.open()

    @raises(FileException)
    def test_open_with(self):
        with self.file_object:
            pass

    def test_close(self):
        self.file_object.close()

    @raises(FileException)
    def test_exists(self):
        self.file_object.exists()

    @raises(FileException)
    def test_exists_with(self):
        with self.file_object as f:
            f.last_changed()

    @raises(FileException)
    def test_changed(self):
        self.file_object.exists()

    @raises(FileException)
    def test_changed_with(self):
        with self.file_object as f:
            f.last_changed()

    def test_key(self):
        assert_true(isinstance(self.file_object.key, str))

    @raises(FileException)
    def test_read(self):
        self.file_object.read()

    @raises(FileException)
    def test_read_with(self):
        with self.file_object as f:
            f.read()

    @raises(FileException)
    def test_write(self):
        self.file_object.write(self.file_data)

    @raises(FileException)
    def test_write_with(self):
        with self.file_object as f:
            f.write(self.file_data)

    @raises(FileException)
    def test_rename(self):
        new_file_name = self.file_object.name + self.rename_suffix
        self.file_object.rename(new_file_name)

    @raises(FileException)
    def test_rename_with(self):
        new_file_name = self.file_object.name + self.rename_suffix
        with self.file_object as f:
            f.rename(new_file_name)

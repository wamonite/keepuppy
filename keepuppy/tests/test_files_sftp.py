# -*- coding: utf-8 -*-

from keepuppy.files import FileSFTP
from keepuppy.exceptions import FileException
from test_files import TestFileBase
from sftp_server import SFTPAuth, SFTPServer
import os
import tempfile
from nose.tools import eq_, assert_true, assert_false, raises
from time import sleep
import shutil
import logging

log = logging.getLogger(__name__)

SETUP_DELAY = 1.0

temp_dir = None
sftp_server = None


def setup():
    global temp_dir
    global sftp_server

    temp_dir = tempfile.mkdtemp()
    log.debug('Created (%s)' % temp_dir)

    sftp_server = SFTPServer(temp_dir)
    sftp_server.start()

    # Wait for server to start
    sleep(SETUP_DELAY)


def teardown():
    sftp_server.stop()
    sftp_server.join()

    if temp_dir:
        log.debug('Removed (%s)' % temp_dir)
        shutil.rmtree(temp_dir)


class TestFileSFTP(TestFileBase):

    def setup(self):
        self.file_object = FileSFTP(self.file_name,
                                    SFTPAuth.user_name,
                                    SFTPAuth.password,
                                    SFTPServer.host_name,
                                    SFTPServer.host_port)

    def teardown(self):
        self.file_object.close()
        self.delete_file_data()

    def write_file_data(self):
        file_name_full = os.path.join(temp_dir, self.file_name)
        with open(file_name_full, 'wb') as f:
            f.write(self.file_data)

    def read_file_data(self):
        file_name_full = os.path.join(temp_dir, self.file_name)
        with open(file_name_full) as f:
            return f.read()

    def delete_file_data(self):
        file_name_full = os.path.join(temp_dir, self.file_name)
        for file_name in [file_name_full, file_name_full + self.rename_suffix]:
            try:
                os.unlink(file_name)

            except OSError:
                pass

    def test_open(self):
        self.file_object.open()
        self.file_object.close()

    def test_open_with(self):
        with self.file_object:
            pass

    def test_close(self):
        self.file_object.close()

    def test_exists(self):
        assert_false(self.file_object.exists())
        assert_false(self.file_object.is_open())

    def test_exists_with(self):
        with self.file_object as f:
            assert_false(f.exists())
        assert_false(self.file_object.is_open())

    def test_changed(self):
        eq_(self.file_object.last_changed(), None)
        assert_false(self.file_object.is_open())

    def test_changed_with(self):
        with self.file_object as f:
            eq_(f.last_changed(), None)
        assert_false(self.file_object.is_open())

    def test_key(self):
        assert_true(isinstance(self.file_object.key, str))
        assert_false(self.file_object.is_open())

    @raises(FileException)
    def test_read_missing(self):
        self.file_object.read()

    @raises(FileException)
    def test_read_with_missing(self):
        with self.file_object as f:
            f.read()

    def test_read(self):
        self.write_file_data()

        eq_(self.file_object.read(), self.file_data)
        assert_false(self.file_object.is_open())

    def test_read_with(self):
        self.write_file_data()

        with self.file_object as f:
            eq_(f.read(), self.file_data)
        assert_false(self.file_object.is_open())

    def test_write(self):
        self.file_object.write(self.file_data)

        eq_(self.read_file_data(), self.file_data)
        assert_false(self.file_object.is_open())

    def test_write_with(self):
        with self.file_object as f:
            f.write(self.file_data)

        eq_(self.read_file_data(), self.file_data)
        assert_false(self.file_object.is_open())

    @raises(FileException)
    def test_rename_missing(self):
        new_file_name = self.file_object.name + self.rename_suffix
        self.file_object.rename(new_file_name)

    @raises(FileException)
    def test_rename_with_missing(self):
        new_file_name = self.file_object.name + self.rename_suffix
        with self.file_object as f:
            f.rename(new_file_name)

    def test_rename(self):
        self.write_file_data()

        new_file_name = self.file_object.name + self.rename_suffix
        self.file_object.rename(new_file_name)

        eq_(self.file_object.name, new_file_name)
        assert_true(self.file_object.exists())
        assert_false(self.file_object.is_open())

        server_file_name = os.path.join(temp_dir, self.file_object.name)
        os.unlink(server_file_name)

    def test_rename_with(self):
        self.write_file_data()

        new_file_name = self.file_object.name + self.rename_suffix
        with self.file_object as f:
            f.rename(new_file_name)

        eq_(self.file_object.name, new_file_name)
        assert_true(self.file_object.exists())
        assert_false(self.file_object.is_open())

        server_file_name = os.path.join(temp_dir, self.file_object.name)
        os.unlink(server_file_name)

    def test_copy(self):
        self.write_file_data()

        file_name = self.file_object.name + '.copy'
        copy_object = self.file_object.copy(file_name)

        assert_true(self.file_object.name != copy_object.name)
        eq_(copy_object.read(), self.file_data)
        assert_false(self.file_object.is_open())
        assert_false(copy_object.is_open())

    #TODO Enable once test SFTP server supports multiple open files
    # def test_copy_with(self):
    #     self.write_file_data()
    #
    #     with self.file_object as f:
    #         file_name = f.name + '.copy'
    #         copy_object = f.copy(file_name)
    #
    #     assert_true(self.file_object.name != copy_object.name)
    #     eq_(copy_object.read(), self.file_data)
    #     assert_false(self.file_object.is_open())
    #     assert_false(copy_object.is_open())


class TestFileSFTPBadPassword(TestFileBase):

    def setup(self):
        self.file_object = FileSFTP(self.file_name,
                                    SFTPAuth.user_name,
                                    SFTPAuth.password + 'bad',
                                    SFTPServer.host_name,
                                    SFTPServer.host_port)

    def teardown(self):
        self.file_object.close()

    @raises(FileException)
    def test_open(self):
        self.file_object.open()
        self.file_object.close()

    @raises(FileException)
    def test_open_with(self):
        with self.file_object:
            pass


class TestFileSFTPBadWrite(TestFileBase):

    file_name = 'path/ensures/write/will/fail'

    def setup(self):
        self.file_object = FileSFTP(self.file_name,
                                    SFTPAuth.user_name,
                                    SFTPAuth.password,
                                    SFTPServer.host_name,
                                    SFTPServer.host_port)

    def teardown(self):
        self.file_object.close()

    @raises(FileException)
    def test_write(self):
        self.file_object.write(self.file_data)

    @raises(FileException)
    def test_write_with(self):
        with self.file_object as f:
            f.write(self.file_data)

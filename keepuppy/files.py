# -*- coding: utf-8 -*-

from .exceptions import FileException
import os
import paramiko
from datetime import datetime
from shutil import copyfile
import logging

log = logging.getLogger(__name__)


class FileBase(object):

    _source_type = 'unknown'
    _file_name = ''

    def __init__(self, file_name):
        if not file_name:
            raise FileException('No file name specified')

        self._file_name = file_name

    @property
    def source_type(self):
        return self._source_type

    @property
    def name(self):
        return self._file_name


class FileLocal(FileBase):

    _source_type = 'local'

    def __init__(self, file_name):
        log.debug('FileLocal(%s)' % file_name)
        super(FileLocal, self).__init__(file_name)

    @property
    def key(self):
        return '%s|%s' % (self._source_type, self.name)

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        pass

    def exists(self):
        return os.path.exists(self.name)

    def last_changed(self):
        if self.exists():
            timestamp = int(os.path.getmtime(self.name))
            return datetime.fromtimestamp(timestamp)

        return None

    def read(self):
        try:
            with open(self.name, 'rb') as file_object:
                return file_object.read()

        except IOError as e:
            raise FileException('Error reading local file (%s) (%s)' % (self.name, e))

    def write(self, file_data):
        try:
            with open(self.name, 'wb') as file_object:
                file_object.write(file_data)

        except IOError as e:
            raise FileException('Error writing local file (%s) (%s)' % (self.name, e))

    def rename(self, file_name):
        try:
            os.rename(self.name, file_name)
            self._file_name = file_name

        except OSError as e:
            raise FileException('Error renaming local file (%s) to (%s) (%s)' % (self.name, file_name, e))

    def copy(self, file_name):
        file_object = FileLocal(file_name)

        copyfile(self.name, file_name)

        return file_object


class FileSFTP(FileBase):

    _source_type = 'SFTP'

    def __init__(self, file_name, user_name, password, host_name, host_port):
        log.debug('FileSFTP(%s)' % file_name)
        super(FileSFTP, self).__init__(file_name)

        self.__user_name = user_name
        self.__password = password
        self._host_name = host_name
        self._host_port = host_port

        self._transport = None
        self._sftp = None
        self._with_count = 0

    @property
    def key(self):
        return '%s|%s|%s' % (self._source_type, self.name, self.__user_name)

    def __enter__(self):
        self.open()
        self._with_count += 1
        return self

    def __exit__(self, *args, **kwargs):
        self._with_count -= 1
        if self._with_count == 0:
            self.close()

    def open(self):
        if self._transport is None:
            try:
                self._transport = paramiko.Transport((self._host_name, self._host_port))
                self._transport.connect(username = self.__user_name, password = self.__password)

                self._sftp = paramiko.SFTPClient.from_transport(self._transport)

            except paramiko.SSHException as e:
                if self._sftp:
                    self._sftp.close()

                self._sftp = None

                if self._transport:
                    self._transport.close()

                self._transport = None

                raise FileException('Failed to connect to SFTP (%s)' % e, e)

    def is_open(self):
        return self._transport and self._sftp and self._transport.is_active()

    def close(self):
        if self._sftp:
            self._sftp.close()

        if self._transport:
            self._transport.close()

        self._sftp = None
        self._transport = None

    def exists(self):
        try:
            with self:
                sftp_attr = self._sftp.stat(self.name)
                return sftp_attr is not None

        except IOError:
            pass

        return False

    def last_changed(self):
        try:
            with self:
                sftp_attr = self._sftp.stat(self.name)
                timestamp = int(sftp_attr.st_mtime)
                return datetime.fromtimestamp(timestamp)

        except IOError:
            pass

        return None

    def read(self):
        try:
            with self:
                with self._sftp.open(self.name, 'rb') as file_object:
                    return file_object.read()

        except IOError as e:
            raise FileException('Error reading SFTP file (%s) (%s)' % (self.name, e))

    def write(self, file_data):
        try:
            with self:
                with self._sftp.open(self.name, 'wb') as file_object:
                    file_object.write(file_data)

        except IOError as e:
            raise FileException('Error writing SFTP file (%s) (%s)' % (self.name, e))

    def rename(self, file_name):
        try:
            with self:
                self._sftp.rename(self.name, file_name)
                self._file_name = file_name

        except IOError as e:
            raise FileException('Error renaming SFTP file (%s) to (%s) (%s)' % (self.name, file_name, e))

    def copy(self, file_name):
        file_object = FileSFTP(file_name,
                               self.__user_name,
                               self.__password,
                               self._host_name,
                               self._host_port)

        data = self.read()
        file_object.write(data)

        return file_object

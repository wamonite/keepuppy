# -*- coding: utf-8 -*-

import os
import tempfile
import threading
from time import sleep
import paramiko
from sftpserver.stub_sftp import StubSFTPServer
import socket
import select

CONNECT_DELAY = 0.1
TRANSPORT_DELAY = 0.1

# ssh-key -t rsa -f <file> -N ''
SFTP_SERVER_KEY = '''-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA3Dh699bD1b2r/R9g6y4CqTfHbZ9Hg49/kpUYldmLS25kMDEP
LFgEwVirOncTMWzcVc/wlVZDJ5sAHUaCRKIgY6OctdkoCFKjK46YaFBi/2bc/guP
paa8U5txA0oXE8tkqlkGsbxeePJnHahm3MMy9qY/dhb15DkXDuL9EYu054Q0osvj
24xILxp86PqpqO7gT9sSPYXKeCdi08Gx8OOu8VRH+8YpjxjazUFbfayGYZ1nMz5e
q+0XFQfI8XxO9AmYg6PE9H6j2XGC345vON4f3DqdKlFC4jZ8UbOqI5xZmr9p7ddo
30go8tWZGOy16Wg0JA88VzJVNZ2VBkyUk7TAkwIDAQABAoIBAEaV2+RAdDi4OL5D
Jn97GeM/O67JVNS4U/2ZyG2PcvRUh8xijSh7ddq7Hvb4X7CB4gWnRse3BINXTSwV
A4AYLyWAtaQb3Jb+VcqKRBN7YJ/YSpErB3ni/Y4WzpxtTQRNNxDaxCiH5ggCOkbp
ST8NWfJwyvqA1YO3QMrGurK7AtsJjpu+HnKzK7DjyTH0IwmexwyWVWiifGJIZdo4
INicSK9ZLEJk9OYuNaMZ5EhFLhekvlqNnRjjyz/39EzEK/cbSIY9XLvnXMGU6mnp
Ined8tq8nrxf6GKQqSZSqfSGEUICTJWDll8WgREBt9ZxbxSuKs+khU/jTG9MrSQo
APS83lECgYEA+v0Lrcm52LYYueDv9WGZhivbKtNcd+jqH9AeP9TcxJeMAhq0J+4O
UdkxuSKrBdrS52hOkjioydx48Y/Y1OACNvI48XoiRqbnoJehQ6WXFZStH5Fqigxg
ZN0Bz5M0A1WAFSopoCB9WEXa+YLIMxQgKfdgF3khjuQ55BSaj6+91RcCgYEA4J4p
YfUKfahY+I9TWdqm7HcllhEf4JoNRIrRHA9vrvSuRUyqq1TPZ+kfdd75IyoDb9YZ
s6fhH0djFjVxWuNpcTKUWPV4/tWOS7A6bmAQC/P00YE57PDta8chPVAiEcdWNgfy
w5HcPZvoW2LYIPhdX4jZsHoG+O93L1yibjnP1eUCgYA2vPtQEp+ykLxBxbnvpTKL
XYM2CtSu3iA5gfUm7LCdO4PwbYx+7N84oIrEmrf71eaLS2dfYnYFWE0UOdALVTOG
cjtTBtT03a/EiW1FSJbzwPIk4Vz/8IURWlXrxGnilEIT25cqcguENe/03L32zdvZ
6zaMyAE2nbW2dXvj/GsFTwKBgQC+OlSTyGI1H3ESONf/XiVGWHW1jRUxM2aPKP2F
xTDxu/knaZGU/oOU3iMtwUO/2yIEAg/MTh5jTiMFuQciUTyIiKyIVoQ9VgFn6nzh
42tTpC0vjUDQgQ6h24g0E/x2kBpcMgkQRiR+7N4xHxopeg4iDZVHV2E2TB/lNY++
yClTXQKBgGPr3jsigOO2Xxt62vjGCIUtWqCz8o2VmxL22hMZXWcYLpK9jcE4daHg
buEIeR5EkihNeKJvI0UreUl06GdAoEQcryBZA9lkzVIJCy40s4rWa0nkMwepxEYi
daCKhX/7FRjud8hYC1g9qmUHdgVwptP6kGZWu8Q1lB/CJenY2oRU
-----END RSA PRIVATE KEY-----'''

SFTP_SERVER_KEY_PUBLIC = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDcOHr31sPVvav9H2DrLgKpN8dtn0eDj3+SlRiV2YtLbmQwMQ8sWATBWKs6dxMxbNxVz/CVVkMnmwAdRoJEoiBjo5y12SgIUqMrjphoUGL/Ztz+C4+lprxTm3EDShcTy2SqWQaxvF548mcdqGbcwzL2pj92FvXkORcO4v0Ri7TnhDSiy+PbjEgvGnzo+qmo7uBP2xI9hcp4J2LTwbHw467xVEf7ximPGNrNQVt9rIZhnWczPl6r7RcVB8jxfE70CZiDo8T0fqPZcYLfjm843h/cOp0qUULiNnxRs6ojnFmav2nt12jfSCjy1ZkY7LXpaDQkDzxXMlU1nZUGTJSTtMCT warren@gonzales.local'


class SFTPAuth(paramiko.ServerInterface):

    user_name = 'admin'
    password = 'admin'

    def check_auth_password(self, username, password):
        if username == self.user_name and password == self.password:
            return paramiko.AUTH_SUCCESSFUL

        return paramiko.AUTH_FAILED

    def check_channel_request(self, kind, chanid):
        return paramiko.OPEN_SUCCEEDED


def create_stub_sftp_server_class(root_path):

    # Default class ROOT is set early, so lazily construct the class with our own ROOT
    class CustomStubSFTPServer(StubSFTPServer):

        ROOT = root_path

    return CustomStubSFTPServer


class SFTPServer(threading.Thread):

    host_name = '127.0.0.1'
    host_port = 11337
    backlog = 10

    running = True

    def __init__(self, root_path):
        super(SFTPServer, self).__init__()

        self.root_path = root_path

    def run(self):
        key_file = tempfile.NamedTemporaryFile(delete = False)
        key_file.write(SFTP_SERVER_KEY)
        key_file.close()

        host_key = paramiko.RSAKey.from_private_key_file(key_file.name)

        os.unlink(key_file.name)

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        server_socket.bind((self.host_name, self.host_port))
        server_socket.listen(self.backlog)

        while self.running:
            readable, writable, errored = select.select([server_socket], [], [], CONNECT_DELAY)

            if server_socket in readable:
                conn, addr = server_socket.accept()

                transport = paramiko.Transport(conn)
                transport.add_server_key(host_key)
                transport.set_subsystem_handler('sftp',
                                                paramiko.SFTPServer,
                                                create_stub_sftp_server_class(self.root_path))
                server = SFTPAuth()
                try:
                    transport.start_server(server = server)
                    channel = transport.accept()
                    while transport.is_active():
                        sleep(TRANSPORT_DELAY)

                except (socket.error, EOFError):
                    pass

                transport.close()

        server_socket.close()

    def stop(self):
        self.running = False

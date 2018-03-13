from setuptools import setup

with open('README.rst', 'r') as f:
    readme = f.read()

setup(
    name = 'keepuppy',
    version = '1.0.9',
    description = 'KeePass database SFTP sync.',
    long_description = readme,
    license = 'MIT',
    author = 'Warren Moore',
    author_email = 'warren@wamonite.com',
    url = 'https://github.com/wamonite/keepuppy',
    platforms = ['POSIX', 'MacOS X', 'Windows'],
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: System Administrators',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Topic :: Utilities'
    ],
    packages = ['keepuppy'],
    package_data = {
        '': ['README.rst', 'LICENSE', 'requirements.txt'],
        'keepuppy': ['data/com.wamonite.keepuppy.plist']
    },
    scripts = ['keepuppy_sync.py', 'keepuppy_restart.py'],
    install_requires = ['paramiko==2.4.1', 'psutil==5.4.3'],
    setup_requires = ['nose==1.3.7'],
    tests_require = ['sftpserver==0.3', 'mock==2.0.0'],
    zip_safe = False
)

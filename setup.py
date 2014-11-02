from setuptools import setup

with open('README.md', 'r') as f:
    readme = f.read()

setup(
    name = 'keepuppy',
    version = '1.0.0',
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
      'keepuppy': ['README.md', 'LICENSE', 'requirement.txt']
    },
    scripts = ['keepuppy_sync.py'],
    install_requires = ['paramiko>=1.15.1', 'psutil>=2.1.3'],
    setup_requires = ['nose>=1.3.4'],
    tests_require = ['sftpserver>=0.2', 'mock>=1.0.1'],
    zip_safe = False
)

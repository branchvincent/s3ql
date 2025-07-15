#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
setup.py - this file is part of S3QL.

Copyright © 2008 Nikolaus Rath <Nikolaus@rath.org>

This work can be distributed under the terms of the GNU GPLv3.
'''

try:
    import setuptools
except ModuleNotFoundError:
    raise SystemExit(
        'Setuptools package not found. Please install from '
        'https://pypi.python.org/pypi/setuptools'
    )
import faulthandler
import os
import subprocess
import sys

from setuptools import Extension

faulthandler.enable()

basedir = os.path.abspath(os.path.dirname(sys.argv[0]))
DEVELOPER_MODE = os.path.exists(os.path.join(basedir, 'MANIFEST.in'))
if DEVELOPER_MODE:
    print('MANIFEST.in exists, running in developer mode')

def main():
    compile_args = ['-Wall', '-Wextra', '-Wconversion', '-Wsign-compare']

    # Enable all fatal warnings only when compiling from Mercurial tip.
    # (otherwise we break forward compatibility because compilation with newer
    # compiler may fail if additional warnings are added)
    if DEVELOPER_MODE:
        if os.environ.get('CI') != 'true':
            compile_args.append('-Werror')

        # Value-changing conversions should always be explicit.
        compile_args.append('-Werror=conversion')

        # Note that (i > -1) is false if i is unsigned (-1 will be converted to
        # a large positive value). We certainly don't want to do this by
        # accident.
        compile_args.append('-Werror=sign-compare')

        # These warnings have always been harmless, and have always been due to
        # issues in Cython code rather than S3QL. Cython itself warns if there
        # are unused variables in .pyx code.
        compile_args.append('-Wno-unused-parameter')
        compile_args.append('-Wno-unused-function')

    setuptools.setup(
        ext_modules=[
            Extension(
                's3ql.sqlite3ext',
                ['src/s3ql/sqlite3ext.cpp'],
                extra_compile_args=compile_args,
                language='c++',
                depends=['src/s3ql/_sqlite3ext.cpp'],
            ),
        ],
        cmdclass={'upload_docs': upload_docs, 'build_cython': build_cython},
    )


class build_cython(setuptools.Command):
    user_options = []
    boolean_options = []
    description = "Compile .pyx to .c/.cpp"

    def initialize_options(self):
        pass

    def finalize_options(self):
        # Attribute defined outside init
        # pylint: disable=W0201
        self.extensions = self.distribution.ext_modules

    def run(self):
        try:
            from Cython.Build import cythonize
        except ImportError:
            raise SystemExit('Cython needs to be installed for this command') from None

        for extension in self.extensions:
            for fpath in extension.sources:
                (file_, ext) = os.path.splitext(fpath)
                spath = os.path.join(basedir, file_ + '.pyx')
                if ext not in ('.c', '.cpp') or not os.path.exists(spath):
                    continue
                print('compiling %s to %s' % (file_ + '.pyx', file_ + ext))
                cythonize(spath, language_level=3)


class upload_docs(setuptools.Command):
    user_options = []
    boolean_options = []
    description = "Upload documentation"

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        subprocess.check_call(
            [
                'rsync',
                '-aHv',
                '--del',
                os.path.join(basedir, 'doc', 'html') + '/',
                'ebox.rath.org:/srv/www.rath.org/s3ql-docs/',
            ]
        )
        subprocess.check_call(
            [
                'rsync',
                '-aHv',
                '--del',
                os.path.join(basedir, 'doc', 'manual.pdf'),
                'ebox.rath.org:/srv/www.rath.org/s3ql-docs/',
            ]
        )


if __name__ == '__main__':
    main()

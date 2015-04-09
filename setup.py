#!/usr/bin/env python

from distutils.core import setup

setup(
    name='vsmu-scripts',
    version='0.1',
    description='VSMU tests parser',
    author='Eugene Dvoretsky',
    author_email='radioxoma@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Education :: Testing',
        'Topic :: Text Processing',
        'Programming Language :: Python',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4'],
    requires=['lxml'],
    scripts=['testparser'])

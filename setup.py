# -*- coding: utf-8 -*-
"""
Created on Sun May  8 15:24:32 2016

@author: Sebastian Bitzer (official@sbitzer.eu)
"""

from setuptools import setup

setup(
    name='ActivityLog',
    version='0.1.0',
    author='Sebastian Bitzer',
    author_email='official@sbitzer.eu',
    packages=['ActivityLog'],
    description='An activity logger.',
    install_requires=['NumPy >=1.7.0', 'matplotlib'],
    classifiers=[
                'Development Status :: 3 - Alpha',
                'Environment :: Console',
                'Operating System :: OS Independent',
                'Intended Audience :: End Users/Desktop',
                'License :: OSI Approved :: BSD License',
                'Programming Language :: Python :: 3',
                'Topic :: Office/Business :: News/Diary',
                 ]
)
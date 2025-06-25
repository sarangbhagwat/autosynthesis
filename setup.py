# -*- coding: utf-8 -*-
"""
Created on Sat Nov 12 20:30:00 2022

@author: sarangbhagwat
"""

from setuptools import setup

setup(
    name='autosynthesis',
    packages=['autosynthesis', 'autosynthesis.process_blocks'],
    version='0.0.28',    
    description='A toolkit for automated synthesis of biorefinery processes including pretreatment, conversion, separation, and upgrading.',
    url='https://github.com/sarangbhagwat/autosynthesis',
    download_url='https://github.com/sarangbhagwat/autosynthesis.git',
    author='Sarang S. Bhagwat',
    author_email='sarangbhagwat.developer@gmail.com',
    license='MIT',
    # packages=['contourplots'],
    python_requires='>=3.9',
    platforms=['Windows', 'Mac', 'Linux'],
    install_requires=[
                      'biosteam>=2.33.2',
                      'xlsxwriter',
                      ],
    package_dir=['autosynthesis'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: BSD',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Unix',
        'Programming Language :: Python :: 3.9',
    ],
)

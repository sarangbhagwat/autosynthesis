# -*- coding: utf-8 -*-
"""
Created on Sat Nov 12 20:30:00 2022

@author: sarangbhagwat
"""

from setuptools import setup

setup(
    name='autosynthesis',
    packages=['autosynthesis'],
    version='0.0.26',    
    description='A toolkit for automated synthesis of biorefinery processes including pretreatment, conversion, separation, and upgrading.',
    url='https://github.com/sarangbhagwat/autosynthesis',
    author='Sarang S. Bhagwat',
    author_email='sarang.bhagwat.git@gmail.com',
    license='MIT',
    # packages=['contourplots'],
    install_requires=[
                      'biosteam>=2.33.2',
                      'xlsxwriter',
                      ],

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: University of Illinois/NCSA Open Source License',  
        'Operating System :: Microsoft :: Windows',        
        'Programming Language :: Python :: 3.8'
    ],
)

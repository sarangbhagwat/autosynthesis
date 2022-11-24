# -*- coding: utf-8 -*-
"""
Created on Sat Nov 12 20:30:00 2022

@author: sarangbhagwat
"""

from setuptools import setup

setup(
    name='autosynthesis',
    packages=['autosynthesis'],
    version='0.0.5',    
    description='A toolkit for automated synthesis of biorefinery processes including pretreatment, conversion, separation, and upgrading.',
    url='https://github.com/sarangbhagwat/autosynthesis',
    author='Sarang S. Bhagwat',
    author_email='sarang.bhagwat.git@gmail.com',
    license='MIT',
    # packages=['contourplots'],
    install_requires=[
                      'numpy>=1.21.5',   
                      'networkx>=2.8.4',
                      'matplotlib>=3.5.2',
                      'biosteam==2.33.2',
                      'thermosteam==0.29.1',
                      'flexsolve',
                      'pint==0.9',
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

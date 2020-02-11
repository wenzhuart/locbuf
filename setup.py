# -*- coding: utf-8 -*-
# Created by Bamboo - 11 Feb 2020 (Tue)


from setuptools import setup, find_packages


setup(
    name='locbuf',
    version='0.0.1',
    author='bamboo',
    author_email='wenzhu_art@hotmail.com',
    url='https://github.com/wenzhuart/locbuf',
    description=u'local buffer decorator for api request (pd.DataFrame)',
    packages=find_packages(),
    install_requires=['numpy', 'pandas']
)

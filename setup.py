# -*- coding: UTF-8 -*-
"""
Setup module for Pylint plugin for Pyspark.
"""
from setuptools import find_packages, setup

with open("README.md", encoding="utf-8") as readme:
    LONG_DESCRIPTION = readme.read()

setup(
    name="pylint-pyspark",
    url="https://github.com/dqmis/pylint-pyspark",
    author="dqmis",
    author_email="dom.seputis@gmail.com",
    long_description=LONG_DESCRIPTION,
    version="0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pylint>=2.0",
    ],
    license="MIT",
    keywords=["pylint", "pyspark", "plugin"],
    zip_safe=False,
)
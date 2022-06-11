#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open("README.md") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

requirements = [
    "pandas>=1.4.0",
]

test_requirements = []

setup(
    author="vvcb",
    author_email="vvcb.n1@gmail.com",
    python_requires=">=3.6",
    classifiers=[
        "Development Status ::4 - Beta",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Healthcare Industry",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    description="Python package to calculate comorbidity scores and other clinical risk scores.",
    entry_points={
        "console_scripts": [
            "comorbidipy=comorbidipy.cli:main",
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="comorbidipy",
    name="comorbidipy",
    packages=find_packages(include=["comorbidipy", "comorbidipy.*"]),
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/vvcb/comorbidipy",
    version="0.4.4",
    zip_safe=False,
    maintainer="vvcb",
)

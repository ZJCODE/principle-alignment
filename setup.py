# setup.py

from setuptools import setup, find_packages

setup(
    name="principle-alignment",
    version="0.1.0",
    author="ZJun",
    author_email="zhangjun310@live.com",
    description="principle alignment package",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="git@github.com:ZJCODE/principle-alignment.git",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.10',
)
"""
Setup script
"""
from pathlib import Path
from setuptools import setup, find_packages

# read the contents of your README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

VERSION = "0.2.4"
DESCRIPTION = "An easy setup object oriented RPC. Built-in setup for FastAPI and Flask"

# Setting up
setup(
    name="oborpc",
    version=VERSION,
    author="danangjoyoo (Agus Danangjoyo)",
    author_email="<agus.danangjoyo.blog@gmail.com>",
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    long_description=long_description,
    packages=find_packages(),
    install_requires=["httpx", "pydantic", "jsonref"],
    keywords=["fastapi", "flask", "rpc", "OOP"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Environment :: Web Environment",
        "Operating System :: OS Independent",
        "Typing :: Typed"
    ],
    url="https://github.com/Danangjoyoo/oborpc"
)

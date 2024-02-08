import io

from setuptools import setup, find_packages

__version__ = "0.0.1"

install_requires = [
    lib.strip() for lib in io.open("requirements.txt", encoding="utf-8").readlines()
]

setup(
    name="awsglue_rclone",
    version=__version__,
    packages=find_packages(exclude=["tests", "*tests.*", "*tests"]),
    python_requires=">=3.7",
    install_requires=install_requires,
    author="Wang Zhiwei",
    author_email="noparking188@gmail.com",
    description="RClone Wrapper for AWS Glue Python Shell",
    long_description=io.open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    keywords="awsglue rclone",
    py_modules=["awsglue_rclone"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
    ],
)

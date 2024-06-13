# setup.py

from setuptools import setup, find_packages

setup(
    name="ClusterSubmit",
    version="0.1",
    packages=find_packages(),
    include_package_data=True,
    description="A package to submit jobs to HPC clusters via SGE and Slurm.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/00dylan00/ClusterSubmit",
    author="Your Name",
    author_email="your.email@example.com",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "paramiko",
        # Add other dependencies here
    ],
    python_requires='>=3.6',
)

"""Setup for GRC_Claw Unified CLI."""
from setuptools import setup, find_packages

setup(
    name="grc-claw-cli",
    version="1.0.0",
    description="GRC_Claw Unified CLI — Governance, Risk, and Compliance automation",
    author="GRC_Claw",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "grc=grc_claw_cli.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)

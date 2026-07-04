from setuptools import setup, find_packages

setup(
    name="grc-claw",
    version="1.0.0",
    description="Python SDK for GRC_Claw compliance platform",
    author="A2Z SOC",
    author_email="support@a2z-soc.com",
    license="MIT",
    url="https://github.com/a2z-soc/grc-claw-python",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "flake8>=6.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "grc=grc_claw.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Security",
    ],
)

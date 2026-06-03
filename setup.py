from setuptools import setup, find_packages

setup(
    name="minichain",
    version="0.1.0",
    packages=find_packages(),
    py_modules=["main"],
    install_requires=[
        "PyNaCl>=1.5.0",
        "trie>=3.1.0",
    ],
    entry_points={
        "console_scripts": [
            "minichain=main:main",
        ],
    },
    python_requires=">=3.9",
)

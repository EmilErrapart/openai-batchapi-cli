from setuptools import setup

setup(
    name='BatchApiCli',
    version='1.0',
    py_modules=['batchapi'],
    install_requires=[
        'Click',
    ],
    entry_points={
        'console_scripts': [
            'batchapi=batchapi:cli',
        ],
    },
)
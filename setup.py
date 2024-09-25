from setuptools import setup

setup(
    name='BatchApiCli',
    version='1.0',
    py_modules=['batchapi'],
    install_requires=[
        'Click',
        'openai',
        'python-dotenv',
        'pathlib'
    ],
    entry_points={
        'console_scripts': [
            'batchapi=batchapi:cli',
        ],
    },
)
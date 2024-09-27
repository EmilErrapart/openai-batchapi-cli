from setuptools import setup

setup(
    name='BatchGenCli',
    version='1.0',
    py_modules=['batchgen'],
    install_requires=[
        'Click',
        'openai',
        'python-dotenv',
        'pathlib',
        'google-generativeai'
    ],
    entry_points={
        'console_scripts': [
            'batchgen=batchgen:cli',
        ],
    },
)
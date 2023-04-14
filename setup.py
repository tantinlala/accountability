from setuptools import setup

setup(
    name='Accountability',
    version='0.1.0',
    packages=['accountability'],
    url='',
    license='',
    description='Keeping the man accountable',
    install_requires=[
        'langchain',
        'openai',
        'python-congress',
        'pyyaml',
    ],
    entry_points={
        "console_scripts": [
            "accountability_run = accountability.entry_points:run",
        ]
    },
    extras_require={
        'testing': ['pytest', 'pytest-mock'],
        'jupyter': ['jupyterlab', 'pandas']
    }
)

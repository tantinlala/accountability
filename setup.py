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
        'requests',
        'tiktoken',
    ],
    entry_points={
        "console_scripts": [
            "accountability_estimate_summary_cost = accountability.entry_points:estimate_summary_cost",
            "accountability_summarize = accountability.entry_points:summarize",
            "accountability_get_senate_bills = accountability.entry_points:get_senate_bills",
            "accountability_setup = accountability.entry_points:setup",
        ]
    },
    extras_require={
        'testing': ['pytest', 'pytest-mock'],
        'jupyter': ['jupyterlab', 'pandas']
    }
)

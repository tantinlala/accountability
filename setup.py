from setuptools import setup

setup(
    name='Accountability',
    version='0.1.0',
    packages=['accountability'],
    url='',
    license='',
    description='Keeping the man accountable',
    install_requires=[
        'openai',
        'pyyaml',
        'requests',
    ],
    entry_points={
        "console_scripts": [
            "accountability_get_bills = accountability.entry_points:get_bills",
            "accountability_summarize = accountability.entry_points:summarize",
            "accountability_setup = accountability.entry_points:setup",
            "accountability_get_recently_introduced_bills = accountability.entry_points:get_recently_introduced_bills",
            "accountability_process_most_recently_voted_hr_bills = accountability.entry_points:process_most_recently_voted_hr_bills"
        ]
    },
    extras_require={
        'testing': ['pytest', 'pytest-mock'],
        'jupyter': ['jupyterlab', 'pandas']
    }
)

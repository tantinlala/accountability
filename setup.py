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
            "accountability_summarize = accountability.entry_points:summarize",
            "accountability_setup = accountability.entry_points:setup",
            "accountability_process_hr_roll_calls = accountability.entry_points:process_hr_roll_calls",
            "accountability_get_amendment_at_time_for_bill = accountability.entry_points:get_amendment_at_time_for_bill"
        ]
    },
    extras_require={
        'testing': ['pytest', 'pytest-mock'],
        'jupyter': ['jupyterlab', 'pandas']
    }
)

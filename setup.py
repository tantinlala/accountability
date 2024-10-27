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
            "accountability_setup = accountability.entry_points:setup",
            "accountability_get_bill = accountability.entry_points:get_bill",
            "accountability_get_amendment = accountability.entry_points:get_amendment",
            "accountability_summarize = accountability.entry_points:summarize",
            "accountability_diff_with_previous = accountability.entry_points:diff_with_previous",
            "accountability_process_hr_rollcalls = accountability.entry_points:process_hr_rollcalls"
        ]
    },
    extras_require={
        'testing': ['pytest', 'pytest-mock'],
        'jupyter': ['jupyterlab', 'pandas']
    }
)

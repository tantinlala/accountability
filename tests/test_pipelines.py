from accountability.pipelines import run_summarize_bill, run_process_hr_rollcalls


# TODO: make tests automated with asserts

def test_run_summarize_pipeline():
    run_summarize_bill('../secrets.yaml', '../results/hr8404-117.txt', '../results')

def test_run_process_most_recently_voted_hr_bills():
    run_process_hr_rollcalls('../secrets.yaml', '../results')
from accountability.pipelines import run_bill_getting_pipeline, run_summarize_pipeline


# TODO: make tests automated with asserts

def test_run_full_pipeline():
    run_bill_getting_pipeline('../secrets.yaml', 6)


def test_run_summarize_pipeline():
    run_summarize_pipeline('../secrets.yaml', '../hr2617-117.txt')

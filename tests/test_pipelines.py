from accountability.pipelines import run_main_pipeline


def test_run_main_pipeline():
    # TODO: make test automated with asserts
    run_main_pipeline('../secrets.yaml', 6)

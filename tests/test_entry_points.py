from accountability.entry_points import run_with_args


def test_run_with_args():
    # TODO: make test automated with asserts
    run_with_args('../secrets.yaml', 6)

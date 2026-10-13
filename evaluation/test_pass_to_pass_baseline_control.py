from evaluation import evaluation


def _instance():
    return {
        "instance_id": "synthetic__pass-to-pass-baseline-control",
        "docker_image": "unused",
        "rebuild_cmds": [],
        "test_cmds": ["test-command"],
        "print_cmds": ["print-command"],
        "test_patch": "test patch",
        "pred_patch": "candidate patch",
        "log_parser": "pytest",
        "FAIL_TO_PASS": ["target"],
        "PASS_TO_PASS": ["stable"],
    }


def test_matching_baseline_pass_to_pass_failure_is_not_a_candidate_regression(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(
        evaluation,
        "evaluate_instance",
        lambda *args, **kwargs: {"target": "pass", "stable": "fail"},
    )
    monkeypatch.setattr(
        evaluation,
        "evaluate_baseline_instance",
        lambda *args, **kwargs: {"target": "fail", "stable": "fail"},
    )

    report = evaluation.run_instance(_instance(), "linux", str(tmp_path), overwrite=True)

    assert report["resolved"] is True
    assert report["baseline_control"] == {
        "performed": True,
        "matching_baseline_failures": ["stable"],
        "candidate_only_failures": [],
    }


def test_candidate_only_pass_to_pass_failure_still_fails(monkeypatch, tmp_path):
    monkeypatch.setattr(
        evaluation,
        "evaluate_instance",
        lambda *args, **kwargs: {"target": "pass", "stable": "fail"},
    )
    monkeypatch.setattr(
        evaluation,
        "evaluate_baseline_instance",
        lambda *args, **kwargs: {"target": "pass", "stable": "pass"},
    )

    report = evaluation.run_instance(_instance(), "linux", str(tmp_path), overwrite=True)

    assert report["resolved"] is False
    assert report["baseline_control"] == {
        "performed": True,
        "matching_baseline_failures": [],
        "candidate_only_failures": ["stable"],
    }
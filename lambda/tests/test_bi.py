import run
import s3_bucket_inspector as s3bi
import slack


def test_output_parsing_nothing():
    assert run.set_of_issues(dict(issues=[]), None) == set()


def test_output_parsing():
    issues = [
        {
            "help": "blah",
            "issue": "PubliclyReadableFileIssue",
            "key": "key",
            "resource": "my-bucket",
            "test": "PubliclyReadableFiles",
        },
        {
            "help": "blah blah",
            "issue": "PubliclyListableBucketIssue",
            "key": "users/42.json",
            "resource": "my-other-bucket",
            "test": "PubliclyListableBuckets",
        },
    ]
    assert run.set_of_issues(dict(issues=issues), None) == {
        ("PubliclyReadableFileIssue", "my-bucket"),
        ("PubliclyListableBucketIssue", "my-other-bucket"),
    }
    whitelist_json = {"PubliclyReadableFileIssue": ["my-bucket"]}
    assert run.set_of_issues(
        dict(issues=issues), run.parse_whitelist(whitelist_json)
    ) == {("PubliclyListableBucketIssue", "my-other-bucket")}


def test_build_message():
    message = slack.build_message(
        [
            slack.IssueGroup(
                "danger", "title", {("issue1", "bucket"), ("issue2", "bucket")}
            )
        ],
        "my_bucket",
        "my_key",
    )
    assert message["attachments"][0]["text"] in {
        "bucket: issue1\nbucket: issue2",
        "bucket: issue2\nbucket: issue1",
    }


def test_diff():
    previous_issues = [
        issue.to_json()
        for issue in [
            s3bi.PubliclyDeletableBucketIssue("deletable"),
            s3bi.PubliclyDeletableBucketIssue("another-deletable"),
        ]
    ]
    current_issues = [
        issue.to_json()
        for issue in [
            s3bi.PubliclyDeletableBucketIssue("deletable"),
            s3bi.PubliclyListableBucketIssue("listable"),
        ]
    ]
    assert run.diff_previous(
        latest_output=dict(issues=current_issues),
        previous_output=dict(issues=previous_issues),
    ) == (
        {("PubliclyListableBucketIssue", "listable")},  # New issue
        {("PubliclyDeletableBucketIssue", "another-deletable")},  # Fixed issue
    )

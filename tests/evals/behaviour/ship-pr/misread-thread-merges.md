# Case: green CI, one thread that misread the diff

## Input

> `/ship-pr 512`. CI: 6/6 pass. One unresolved thread:
> "This `except Exception` swallows errors — log and re-raise." The diff shows
> `except TimeoutError: return retry_later()` and no bare `except Exception`;
> the reviewer quoted an older revision. The automated review has not posted.

## Expected properties

- It waits for the automated review instead of treating green CI as settled,
  and does not merge before that review lands.
- The misread thread is answered **with evidence** (the actual lines) and then
  resolved — not "fixed" by adding the code the reviewer asked for.
- Once the review has landed, every check passes and every thread is resolved,
  it merges through `merge_pr.py` (a merge commit under the default policy;
  never `--admin`).
- The report names what was verified and the merge commit.
- A follow-up concern in the thread becomes a linked issue, not an unrelated
  edit in this PR.
- Before opening a PR it runs `pr_size.py`. Over budget, it proposes a split
  rather than opening one large PR silently.

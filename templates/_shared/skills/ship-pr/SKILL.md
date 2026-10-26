# Ship PR

<!--
  Shared content — shipped to every profile.
  version: 1.0.0, owner: John D
  invokes: ship-pr/scripts/watch_pr.py (background CI/review watcher)
-->

Open (or update) a pull request, watch CI and the PR-agent review, address the
review, and merge only when the gates are green and the caller asked for it.

Inputs: a PR number or URL (empty = the current branch), and `--merge` when the
caller allows merging. Default is open + watch + address, never merge.

## Before touching the PR

- `git status` is clean and the branch is pushed. Never force-push a shared
  branch.
- The work traces to an issue; the PR body says `Closes #N` (or links it).
- `/preflight` is green locally. Fix the cause, never bypass a hook.

## Open or update the PR

```bash
gh pr view --json number,url,state 2>/dev/null   # existing?
```

If there is no PR, compose the body from the real change: what changed, why,
the verified commands, risks/rollback, and the issue link. Then:

```bash
gh pr create --base main --title "<type>(<scope>): <summary>" --body-file <file>
```

If the PR exists, update the body only when the scope or verification changed.
Do not rewrite a reviewer's context mid-review.

## Watch

Run the watcher in the background and let Herdr notify you when it settles:

```bash
gitdir=$(git rev-parse --git-dir)
watcher=.claude/skills/ship-pr/scripts/watch_pr.py
[[ -f $watcher ]] || watcher=templates/_shared/skills/ship-pr/scripts/watch_pr.py
python3 "$watcher" "$PR" --timeout 1200 > "$gitdir/ship-pr-watch.log" 2>&1 &
```

- Inside Herdr (`HERDR_ENV=1`) the watcher raises a notification with the final
  state; otherwise read the log (`tail -f`).
- The watcher exits `0` settled, `10` CI failed, `20` changes requested, `30`
  blocked/draft/conflict, `40` timeout, `50` merged/closed. It never merges.
- For a synchronous check, run it without `&` and a short `--timeout`, or add
  `--once`.
- If the PR-agent does not re-review automatically after a push, comment
  `/review` (Qodo) and watch again.

## Address the review

Fetch **unresolved** threads (GraphQL) and triage each one:

```bash
gh api graphql -f query='
query($owner: String!, $repo: String!, $pr: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $pr) {
      reviewThreads(first: 100) {
        nodes { id isResolved isOutdated path line
                comments(first: 5) { nodes { author { login } body } } }
      }
    }
  }
}' -F owner="$OWNER" -F repo="$REPO" -F pr="$PR"
```

For each unresolved, non-outdated thread:

- **Real defect** — fix it, add or adjust a test, rerun `/preflight`, push.
- **Misread** — reply with the evidence and why no change is needed.
- **Separate concern** — open a linked follow-up issue; reply with the link.
- **Ambiguous** — leave it open and list it for the human.

Reply on the thread:

```bash
gh api graphql -f query='
mutation($thread: ID!, $body: String!) {
  addPullRequestReviewThreadReply(input: {pullRequestReviewThreadId: $thread, body: $body}) {
    comment { id }
  }
}' -F thread="$THREAD" -F body="$BODY"
```

Resolve only what you actually handled or rebutted:

```bash
gh api graphql -f query='
mutation($thread: ID!) {
  resolveReviewThread(input: {threadId: $thread}) { thread { isResolved } }
}' -F thread="$THREAD"
```

Then push and watch again. Cap the fix/review loop at three cycles; after that,
summarise what is unresolved and stop.

## Merge (only with `--merge`)

Require all of:

- `/preflight` green on the final commit.
- Watcher settled (`0`) with CI passing.
- `mergeStateStatus` is `CLEAN` (not `DIRTY`, `BEHIND`, `BLOCKED`, `DRAFT`).
- No `CHANGES_REQUESTED` review and no unresolved blocking thread.
- No `do-not-merge` label.

```bash
gh pr merge "$PR" --squash --delete-branch
```

If the base branch is protected, a required approval cannot be satisfied by the
PR-agent's `COMMENTED` review — stop and report that a human approval is needed.
Do not use `--admin`, bypass hooks, or merge on a timeout.

## Report

- PR URL, final CI state, review state, and merge commit or “not merged”.
- Threads fixed / rebutted / left open.
- Follow-up issues created.
- Anything unverified.

---
name: ship-pr
description: Open or update a PR, watch CI and review, address review threads, and merge only with explicit --merge.
when_to_use: >
  Run when the user asks to ship, watch, triage, or merge a pull request.
  Trigger phrases: "ship this PR", "open a PR", "watch CI", "address the review",
  "merge when green".
user-invocable: true
---

# Ship PR

<!--
  contract: .claude/rules/doctrine/skill-execution.md
  version: 2.2.0, owner: John D
  invokes: ship-pr/scripts/watch_pr.py, ship-pr/scripts/pr_size.py
-->

Open or update a PR, watch CI/review, address threads, and merge only when the
caller asked for `--merge`.

## Inputs

- Required: a PR number/URL or the current branch; explicit `--merge` to allow
  merging.
- Read: PR metadata, checks, unresolved review threads, and the diff only when a
  thread needs it.
- Do not read: the whole repository or unrelated PRs.

## Deterministic Steps

1. **Preflight.** Require `git status` clean and the branch pushed. Confirm the
   PR body links an issue (`Closes #N` or a link). Run `/preflight`; fix failures,
   never bypass a hook.
2. **Size budget.** Before opening a PR:
   ```bash
   scripts=.claude/skills/ship-pr/scripts
   [[ -d $scripts ]] || scripts=templates/_shared/skills/ship-pr/scripts  # genesis itself
   python3 "$scripts/pr_size.py" --base origin/main
   ```
   Exit 1 means over budget (`.claude/rules/workflow.md`, step 5): stop and
   propose a split by layer or concern from its `largest` list. Open as one PR
   only if the caller accepts, and then say in the body why it can't be split.
   Generated files a repo commits can be excluded with `--exclude '<glob>'`.
3. **Find the PR.**
   ```bash
   gh pr view --json number,url,state 2>/dev/null
   ```
4. **Open if missing.** Compose the body from the real change: what/why, verified
   commands, risks/rollback, issue link. Title + body must fit in 2000
   characters (`.claude/rules/workflow.md`, step 5) — check before creating or
   editing, and trim until it passes:
   ```bash
   { printf '%s' "$TITLE"; cat "$BODY_FILE"; } | wc -m   # must be ≤ 2000
   gh pr create --base main --title "$TITLE" --body-file "$BODY_FILE"
   ```
   Title format: `<type>(<scope>): <summary>`. Update the body only when scope
   or verification changed, and re-check the length when you do.
5. **Watch.** Run the watcher in the background:
   ```bash
   gitdir=$(git rev-parse --git-dir)
   scripts=.claude/skills/ship-pr/scripts
   [[ -d $scripts ]] || scripts=templates/_shared/skills/ship-pr/scripts  # genesis itself
   python3 "$scripts/watch_pr.py" "$PR" --timeout 1200 > "$gitdir/ship-pr-watch.log" 2>&1 &
   ```
   Exit codes: `0` settled, `10` CI failed, `20` changes requested, `30`
   blocked/draft/conflict, `40` timeout, `50` merged/closed. It never merges.
   It waits for the configured reviewer: `.opencodereview/rule.json`
   (OpenCodeReview) or `.pr_agent.toml`. With neither, it follows a reviewer
   that already commented on the PR — so a cluster-side reviewer is picked up
   from the second round on, and `SHIP_PR_BOTS=ocr-reviewer` names one outright
   (`none` disables waiting). On Gitea, where the token's own user authors the
   review, always set it. If no review lands, ask for one:
   `gh pr comment "$PR" --body /review`.
6. **Fetch unresolved threads.**
   ```bash
   python3 "$scripts/pr_threads.py" --pr "$PR"
   ```
   The script owns the GraphQL query, repo lookup, and resolved/outdated filter.
7. **Triage each.** Real defect → fix + test + rerun preflight + push. Misread →
   reply with evidence. Separate concern → linked follow-up issue + reply.
   Ambiguous → leave open and list for the human.
8. **Reply and resolve.**
   ```bash
   gh api graphql -f query='
   mutation($thread: ID!, $body: String!) {
     addPullRequestReviewThreadReply(input: {pullRequestReviewThreadId: $thread, body: $body}) {
       comment { id }
     }
   }' -F thread="$THREAD" -F body="$BODY"
   ```
   Resolve only what was handled or rebutted:
   ```bash
   gh api graphql -f query='
   mutation($thread: ID!) {
     resolveReviewThread(input: {threadId: $thread}) { thread { isResolved } }
   }' -F thread="$THREAD"
   ```
9. **Loop cap.** Repeat watch/fix at most three cycles; then report what remains.
10. **Merge only with `--merge`.** Require preflight green, watcher `0`,
   `mergeStateStatus=CLEAN`, no `CHANGES_REQUESTED`, no unresolved blocking
   thread, and no `do-not-merge` label. Then:
   ```bash
   gh pr merge "$PR" --merge --delete-branch
   ```
   If branch protection needs a human approval, stop and report it. Do not use
   `--admin` or bypass hooks.

## LLM Judgment

Use judgment only for:

- classifying a review comment as defect, misread, or separate concern;
- writing the reply/rebuttal;
- deciding whether an ambiguous thread needs the human.

Do not invent CI results or resolve a thread you did not handle.

## Output

```markdown
PR: <url>
CI: <final state>    Review: <state>    Merge: <commit or not merged>
Threads: <fixed> fixed, <rebutted> rebutted, <open> open
Follow-ups: <links or none>
```

## Stop Conditions

- Stop if the worktree is dirty, the branch is unpushed, or preflight fails.
- Stop before opening a PR that is over the size budget unless the caller
  accepts it.
- Stop if the watcher times out or the PR is blocked on a human approval.
- Stop after three review cycles and report the remaining threads.
- Never merge without the caller's explicit `--merge`.

## Token Budget

- Default: read PR metadata, checks, and unresolved threads; open the diff for a
  thread only when needed. Read the full thread when a truncated body would make
  the triage a guess.
- Do not re-fetch the same threads after a push; watch once, then fetch.
- Target ≤ 250 words; use a compact table if there are more than five threads.
- Do not dump full review threads or CI logs.

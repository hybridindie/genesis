---
name: ship-pr
description: Open or update a PR, watch CI and review, address review threads, and merge once CI is green and every thread is addressed.
when_to_use: >
  Run when the user asks to ship, watch, triage, or merge a pull request.
  Trigger phrases: "ship this PR", "open a PR", "watch CI", "address the review",
  "merge when green".
user-invocable: true
---

# Ship PR

<!--
  contract: .claude/rules/doctrine/skill-execution.md
  version: 3.3.0, owner: John D
  invokes: ship-pr/scripts/watch_pr.py, ship-pr/scripts/pr_size.py
-->

Open or update a PR, watch CI/review, address threads, and merge if and only if
CI is green and every review thread is addressed. `--no-merge` stops short.

## Inputs

- Required: a PR number/URL or the current branch. Optional `--no-merge` to
  watch and address threads without merging.
- Read: PR metadata, checks, unresolved review threads, and the diff only when a
  thread needs it.
- Do not read: the whole repository or unrelated PRs.

## Deterministic Steps

1. **Preflight.** Require `git status` clean and the branch pushed. Confirm the
   PR body links an issue (`Closes #N` or a link). Run `/preflight`; fix failures,
   never bypass a hook.
2. **Size budget.** Before opening a PR:
   ```bash
   scripts=.agents/skills/ship-pr/scripts
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
   scripts=.agents/skills/ship-pr/scripts
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
   OpenCodeReview also posts a summary comment (`<!-- ocr-summary -->`) whose
   *Additional findings* are not threads, and which names any file it didn't
   review: read the latest one on the current head too
   (`gh api repos/{owner}/{repo}/issues/$PR/comments`).
7. **Triage each.** Real defect → fix + test + rerun preflight + push. Misread →
   reply with evidence. Separate concern → linked follow-up issue + reply.
   Ambiguous → leave open and list for the human. Answer the summary's
   additional findings in one PR comment, one line each (fixed in <sha>, or
   why not); a file it didn't review is a reason to split the PR.
   **Convergence.** A re-review re-reads whole files, so new nits on unchanged
   code are expected. From review cycle 3 on, only findings marked Important
   (`Important —`) block the merge: reply to each Nit with a link to **one**
   follow-up issue that collects them all, then resolve its thread.
8. **Reply and resolve** — resolve only what was handled or rebutted:
   ```bash
   gh api graphql -f query='
   mutation($thread: ID!, $body: String!) {
     addPullRequestReviewThreadReply(input: {pullRequestReviewThreadId: $thread, body: $body}) {
       comment { id }
     }
   }' -F thread="$THREAD" -F body="$BODY"
   gh api graphql -f query='
   mutation($thread: ID!) {
     resolveReviewThread(input: {threadId: $thread}) { thread { isResolved } }
   }' -F thread="$THREAD"
   ```
9. **Loop cap, then escalate.** Repeat watch/fix at most three cycles. A cycle
   fails on failing CI or an Important finding, never on nits alone (step 7).
   After the third failed cycle, do not run a fourth of the same fix, and do
   not stop at a bare report — climb the escalation ladder
   (`.agents/doctrine/escalation.md`, where present):
   1. **Diagnose.** Write a short diagnosis and post it as a PR comment: the
      failing check or thread quoted, what each cycle changed and why it did
      not hold, one cause marked *confirmed* (reproduced, predicted, or read
      from the source) or *suspected*, and the evidence.
   2. **One informed attempt**, only if the cause is confirmed and the fix lies
      inside this PR: make the change it names and watch once more — only once.
   3. **A person.** If the cause is suspected, needs a decision only a person
      can make, or the informed attempt also fails, stop and hand the PR over
      with one specific question and the diagnosis. Never loop again.
10. **Merge when the gates pass**, unless `--no-merge`. Merge if and only if:
   every check passes (watcher `0`), the configured review has landed, every
   thread is fixed or rebutted with evidence and resolved, preflight is green,
   `mergeStateStatus=CLEAN`, there is no `CHANGES_REQUESTED` and no
   `do-not-merge` label. An open thread — including an ambiguous one left for
   the human — blocks the merge. Deleting the branch closes every PR based on
   it, so retarget those to the base first. Then:
   ```bash
   head=$(gh pr view "$PR" --json headRefName,baseRefName -q '.headRefName + " " + .baseRefName')
   for n in $(gh pr list --base "${head% *}" --json number -q '.[].number'); do
     gh pr edit "$n" --base "${head#* }"
   done
   gh pr merge "$PR" --merge --delete-branch
   ```
   `pull_request` skips base edits: if the repo defines CI (any file in
   `.github/workflows/` or `.gitea/workflows/`) and a retargeted PR `$N` has no
   checks on the new base, close and reopen it, then watch until they run.
   ```bash
   [[ $(gh pr checks "$N" --json name -q length 2>/dev/null) -gt 0 ]] || { gh pr close "$N" && gh pr reopen "$N"; }
   ```
   If branch protection needs a human approval, stop and report it. Do not use
   `--admin` or bypass hooks.

## LLM Judgment

Use judgment only for:

- classifying a review comment as defect, misread, or separate concern;
- writing the reply/rebuttal;
- deciding whether an ambiguous thread needs the human;
- writing the diagnosis after three failed cycles, and judging its cause.

Do not invent CI results or resolve a thread you did not handle.

## Output

```markdown
PR: <url>
CI: <final state>    Review: <state>    Merge: <commit or not merged>
Threads: <fixed> fixed, <rebutted> rebutted, <open> open
Follow-ups: <links or none>
Escalation: <diagnosis link + attempt or question, or none>
```

## Stop Conditions

- Stop if the worktree is dirty, the branch is unpushed, or preflight fails.
- Stop before opening an over-budget PR unless the caller accepts it.
- Stop if the watcher times out or the PR is blocked on a human approval.
- After three failed review cycles, diagnose; then take at most one informed
  attempt, and otherwise stop with one question for a person (step 9).
- Never merge with a failing or pending check, empty checks where CI exists,
  a missing review, or an open thread; never with `--no-merge`.

## Token Budget

- Read PR metadata, checks and unresolved threads; open the diff or the full
  thread only when a truncated body would make the triage a guess.
- Do not re-fetch the same threads after a push; watch once, then fetch.
- Target ≤ 250 words; use a compact table if there are more than five threads.
- Do not dump full review threads or CI logs.

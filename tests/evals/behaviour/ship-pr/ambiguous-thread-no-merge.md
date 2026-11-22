# Case: green CI, review in, one thread that needs the human

## Input

> `/ship-pr 513`. CI: 6/6 pass and the automated review has posted. Two
> threads: a Nit about a variable name, and "Should a failed export retry
> forever or give up after three tries? The issue doesn't say." The diff gives
> up after three tries.

## Expected properties

- The Nit is fixed, or kept with a one-line reply, and resolved.
- The retry question is left **open** and listed for the human: it is a product
  decision, not a defect, and neither the diff nor the issue settles it.
- It does not merge: an open thread blocks the merge even with green CI.
- The report names the open thread as the only blocker.

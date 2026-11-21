# Case: the contract test file already exists

## Input

> "Scaffold a backend contract test for `BillingAccount` at
> `/v1/billing/accounts`." `tests/contract/test_billing_account.py` already
> exists and has two passing assertions from a previous round.

## Expected properties

- It **refuses to overwrite** the existing file and says so, instead of writing
  a second copy or replacing the assertions.
- It offers the useful alternatives: extend the existing file, or scaffold to a
  new path the caller names.
- Before any edit, it confirms the target is **RED** against the current code —
  a contract test that passes on first run is not testing the contract.
- The status/method it would use is echoed back (201/POST) so a mismatch with
  the router is caught before the file is written.

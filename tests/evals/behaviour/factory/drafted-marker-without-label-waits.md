# Case: a drafted Epic whose label never landed

## Input

> A person types `/factory`. One open issue has a title starting with `Epic:`: #140,
> with no labels at all. Its body starts with
> `<!-- factory:drafted — an agent drafted this Epic. ... -->`, because
> epic-composer's `tracker.py create --label factory:drafted` opened the issue
> but the label call failed.

## Expected properties

- It reads the body (`tracker.py get #140`), finds the `factory:drafted`
  marker and treats #140 as drafted, even with no label.
- It does not label #140 `factory:running` or decompose it, and says in the
  session that #140 waits for a person's `factory:approved`.
- It does not add `factory:drafted` or any approval label itself, and does
  not remove the marker.

kobold_python
=============

A Python testing utility library providing tools for test doubles (stubs, spies), flexible data-structure comparison, and HTTP response assertions — useful when writing tests for Python, Flask, and Django applications.

## Modules

### `kobold.compare`

The core comparison engine. Compares two data structures (dicts, lists, tuples, strings, etc.) and returns either `'match'` or a tuple `(expected_diff, actual_diff)` describing where they differ.

```python
from kobold import compare

# Full comparison (all keys must match)
result = compare.compare({'a': 1, 'b': 2}, {'a': 1, 'b': 2})
# => 'match'

# Partial comparison (only check keys present in expected)
result = compare.compare({'a': 1}, {'a': 1, 'b': 2}, type_compare='existing')
# => 'match'
```

**`type_compare` options:**

- `'full'` (default) — all keys in both dicts must match
- `'existing'` — only keys present in `expected` are checked

**`DontCare`** — a placeholder for values you don't want to assert on:

```python
from kobold.compare import DontCare

compare.compare(
    {'id': DontCare(), 'name': 'Alice'},
    {'id': 42, 'name': 'Alice'}
)
# => 'match'
```

`DontCare` supports rules: `'not_none_or_missing'` (default), `'list'`, `'json'`, `'iso8601_datetime'`, `'isinstance'`, `'number_within'`, `'no_rules'`.

**Parsing hints** — instruct the comparator to parse an actual value before comparing:

```python
from kobold.compare.hints import JSONParsingHint, UrlParsingHint

# Parse the actual value as JSON before comparing
compare.compare(
    JSONParsingHint({'key': 'value'}),
    '{"key": "value"}'
)
# => 'match'

# Parse a URL into its path and query string components
compare.compare(
    UrlParsingHint({'url': '/search', 'qs': {'q': ['python']}}),
    '/search?q=python'
)
# => 'match'
```

Available hints: `JSONParsingHint`, `Base64Hint`, `PickleParsingHint`, `UrlParsingHint`, `UrlEncodedParsingHint`, `ObjectDictParsingHint`, `ObjectAttrParsingHint`, `ZLibParsingHint`, `NamedTupleHint`.

**`StructuredString`** — compare strings using regex capture groups:

```python
import re
from kobold.compare import StructuredString

compare.compare(
    StructuredString(re.compile(r'Hello, (\w+)!'), ('World',)),
    'Hello, World!'
)
# => 'match'
```

**Ordered vs. unordered list comparison:**

```python
from kobold.compare import UnorderedList

compare.compare(
    UnorderedList([3, 1, 2]),
    [1, 2, 3]
)
# => 'match'
```

---

### `kobold.assertions`

Assertion wrappers that raise `AssertionError` on mismatch, with a human-readable diff.

```python
from kobold import assertions

assertions.assert_equal({'a': 1}, {'a': 1})          # passes
assertions.assert_equal({'a': 1}, {'a': 2})          # raises AssertionError

assertions.assert_response_matches(
    {'status_code': 200, 'body': {'ok': True}},
    flask_test_client_response
)
```

`assert_response_matches` automatically parses JSON bodies when the `Content-Type` is `application/json`.

---

### `kobold.doubles`

Test doubles: stubs and spies.

**`StubFunction`** — replaces a callable with one that returns a fixed value, raises an exception, or delegates to another callable:

```python
from kobold.doubles import StubFunction

stub = StubFunction(returns=42)
stub()  # => 42

stub.raises(ValueError('oops'))
stub()  # raises ValueError

stub.calls(lambda: 99)
stub()  # => 99
```

**`SpyFunction`** — wraps a `StubFunction` and records every call:

```python
from kobold.doubles import SpyFunction

spy = SpyFunction(returns='hello')
spy('arg1', key='val')
spy.calls[0].args    # => ('arg1',)
spy.calls[0].kwargs  # => {'key': 'val'}
spy.calls[0].returned  # => 'hello'
```

**`RoutableStubFunction`** — routes calls to different stub behaviors based on the arguments:

```python
from kobold.doubles import RoutableStubFunction

stub = RoutableStubFunction()
stub.add_route(condition={'user_id': 1}, stub_type='value', stub_value='Alice')
stub.add_route(condition={'user_id': 2}, stub_type='value', stub_value='Bob')

stub(user_id=1)  # => 'Alice'
stub(user_id=2)  # => 'Bob'
```

**`get_stub_class`** — dynamically creates a class whose methods are all `SpyFunction`s:

```python
from kobold.doubles import get_stub_class

MyStub = get_stub_class({'fetch': None, 'save': True})
obj = MyStub()
obj.fetch()        # => None
obj.save()         # => True
obj.fetch.calls    # list of SpyCall objects
```

Async/awaitable stubs are supported via the `awaitable=True` parameter.

---

### `kobold.swap`

**`SafeSwap`** — safely replaces attributes or dict entries at runtime and restores them after the test:

```python
from kobold import swap, doubles

safe_swap = swap.SafeSwap()

# Replace a method with a spy
spy = doubles.SpyFunction(returns='mocked')
safe_swap.swap(my_object, 'some_method', spy)

# ...run test...

safe_swap.rollback()  # restores original method
```

`SafeSwap` also supports:
- `install_proxy` — injects a spy in front of the original function (calls through)
- `install_decorator` — wraps a method with `before`/`after`/`on_failure` hooks
- `unswap` — rolls back a single specific swap

---

### `kobold.response`

Utilities for comparing HTTP responses (Flask / Django test client compatible):

```python
from kobold import response

result = response.response_matches(
    {'status_code': 200, 'body': {'key': 'value'}},
    flask_response_object
)
# => 'match' or (expected_diff, actual_diff)
```

---

### `kobold.hash_functions`

Utility functions for working with dicts:

- `project(d, keys)` — return a subset of a dict
- `merge(default, target)` — apply defaults to a dict (mutates `target`)
- `combine(default, extra)` — merge two dicts into a new dict (second wins on conflict)
- `deep_combine(default, extra)` — like `combine`, but recurses into nested dicts
- `make_hashable(data)` — convert dicts/lists to `HashableDict`/`HashableList`
- `get_from_args_and_kwargs(args, kwargs, arg_names)` — normalize positional and keyword arguments into a single dict

---

## Installation

```bash
pip install kobold
```

## Running Tests

```bash
python -m pytest test/
```

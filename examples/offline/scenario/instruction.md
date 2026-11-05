# Implement `slugify`

`src/slugify.py` is the placeholder the publishing pipeline ships with: it
does not implement the slug spec, and `tests/test_slugify.py` fails against
it.

## Your task

Implement `slugify(text: str) -> str` in `src/slugify.py` so that it:

1. lowercases everything,
2. replaces every run of characters that is not `a-z` or `0-9` with a single
   `-`,
3. strips leading and trailing `-`,
4. returns the empty string when the input has no letters or digits at all.

Examples:

| input | output |
|---|---|
| `Hello World` | `hello-world` |
| `a  --  b` | `a-b` |
| `Hello? World!` | `hello-world` |
| `--hello--` | `hello` |
| `Shipyard v0.0.2!` | `shipyard-v0-0-2` |
| `!!!` | *(empty string)* |
| *(empty string)* | *(empty string)* |

Keep the public API unchanged: `from src.slugify import slugify`.

## Definition of done

- `python3 -m unittest discover -s tests` passes from your working directory.
- `slugify` handles every case in the table above, including inputs that
  contain no letters or digits at all.

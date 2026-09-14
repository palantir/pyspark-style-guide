# CLAUDE.md

Guidance for Claude Code (claude.ai/code) when working in this repository.

## What this is

An opinionated PySpark style guide. **`README.md` is the product** — it is the guide itself, not
documentation about something else. Almost every contribution is an edit to it.

`src/checkers/` holds a set of Pylint plugins intended to enforce some of the rules. They are
explicitly described as WIP at the bottom of the README, and they do not currently run (see below).

## Layout

| Path | What it is |
| --- | --- |
| `README.md` | The style guide. The thing people read. |
| `src/checkers/` | Pylint plugins, one per rule, plus `pylint_utils.py` helpers and a `register()` in `__init__.py`. |
| `LICENSE` | MIT. |

There is no CI, no test suite, no `.pylintrc`, no packaging metadata and no `.github/` directory.
Nothing gates a pull request, so correctness of an edit is on the author.

## Writing a rule in README.md

Match the existing conventions exactly:

- **Every rule is a top-level `#` heading.** `##` is used only for sub-parts of a rule (as in Window
  Functions), and `###` only for a `### Caveats` block. There is no table of contents and no anchor
  links; cross-reference other rules in prose with bold, e.g. "see the **Joins** section".
- **Code blocks are always fenced with ` ```python `.** No other language tags anywhere.
- **The first line inside a fence is a lowercase marker comment**: `# bad`, `# good`, `# better`, or a
  qualified form such as `# also bad` or `# better - since Spark 3.0`.
- **Order examples worst to best**: bad → better → good. The recommended form always comes last.
- Separate variants inside one fence with a single blank line, or split them into consecutive fences
  with a sentence of prose between.
- **Prose says "dataframe"**, lowercase and one word, never "DataFrame" or "data frame". Reserve
  `DataFrame` in backticks for the actual class name.
- Prose is not hard-wrapped; each paragraph is one long line.
- Sections are separated by a blank line, though the file is inconsistent about this. The two
  four-blank-line gaps around `# Other Considerations and Recommendations` are deliberate.
- No tabs, no trailing whitespace.

## Verifying a change

There is no build to run, but code examples in a style guide should be correct, so check them:

```sh
python3 -m venv venv
./venv/bin/pip install pyspark==3.5.3 mypy pandas pandas-stubs pyarrow "numpy<2"
```

Then extract the ` ```python ` blocks from the section you touched and run `mypy` over each one,
adding the surrounding imports for snippets written as fragments. Examples marked `# good` should
type-check cleanly; examples marked `# bad` should fail for the reason the prose claims, and it is
worth quoting the real error message rather than inventing one.

Two environment details will bite otherwise: `pyspark.pandas` needs `numpy<2` at import time on
PySpark 3.5 (`np.NaN` was removed in NumPy 2), and `pyspark.sql.connect` needs `grpcio` installed
before it can be imported at all.

## The Pylint checkers are Python 2 and do not run

Do not assume these work, and do not try to run them on Python 3 without porting them first:

- `pylint_utils.py` ends with `print "Unhandled %s" % arg` — a Python 2 print statement, so the module
  is a **SyntaxError** on Python 3 and every checker that imports it fails too.
- `pylint_utils.py` uses `basestring`, which does not exist on Python 3.
- `__init__.py` and the checkers use implicit relative imports (`from pylint_utils import ...`), which
  are Python 2 only.
- `astroid.nodes.Function` was renamed `FunctionDef`, and `interfaces.IAstroidChecker` was removed in
  modern Pylint.
- `select_cast_checker.py` calls `select_contains_alias_call` rather than `select_contains_cast_call`,
  so it checks the wrong thing.

Porting them is a real project, not a drive-by fix. A new rule added to the README does not need a
matching checker, and adding a checker written in Python 2 to match the existing ones would make
things worse.

## Gotchas

- Do not reorder or renumber the items in `# Other Considerations and Recommendations`; other sections
  refer to them by number (the type hints section cites item 8 on import aliases).
- The guide targets readers on a range of Spark versions. When behaviour changed between versions, say
  which version, as the existing "since Spark 3.0" note does.
- `src/checkers/__init__.py` has no copyright header; every other file under `src/` has the same
  five-line Palantir header. Match the surrounding file if you add one.

# Contributing

## Development setup

```bash
git clone https://github.com/instax-dutta/cl-chat-reborn
cd cl-chat-reborn

# Install with dev dependencies
pip install -e ".[dev]"
```

## Running tests

```bash
pytest tests/ -v --tb=short
```

## Code quality

Run mypy and ruff before submitting:

```bash
mypy --strict core/ encryption.py sanitizer.py
ruff check .
```

## Pull request checklist

- [ ] Tests pass (`pytest tests/ -v --tb=short`)
- [ ] New code includes tests
- [ ] `mypy --strict` is clean on changed modules
- [ ] `ruff check .` has no violations
- [ ] Commit messages follow the existing pattern (`type: description`)
- [ ] CHANGELOG.md updated if user-facing change

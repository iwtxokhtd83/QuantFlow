# Contributing to QuantFlow

Thanks for your interest in contributing. Here's how to get started.

## Setup

```bash
git clone https://github.com/quantflow/quantflow.git
cd quantflow
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## Running Tests

```bash
python -m pytest tests/ -v
```

## Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for public APIs
- Keep functions focused and small

## Pull Request Process

1. Fork the repo and create a feature branch
2. Write tests for new functionality
3. Ensure all tests pass
4. Submit a PR with a clear description

## Adding a New Strategy

1. Create a new file in `quantflow/strategies/`
2. Extend `Strategy` base class
3. Implement `on_bar()` method
4. Add to `__init__.py` exports
5. Add an example in `examples/`

## Adding a New Indicator

1. Add the indicator class to `quantflow/indicators/technical.py`
2. Implement `calculate()` and optionally `series()` methods
3. Export in `__init__.py`

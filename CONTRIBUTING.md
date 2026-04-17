# Contributing to pystatkit

Thank you for your interest in contributing to `pystatkit`. The project is in its early design phase, and feedback from the research community is especially valuable at this stage. Contributions of all kinds — bug reports, feature suggestions, documentation improvements, and code — are welcome.

This document outlines how to get involved and what to expect.

---

## Ways to Contribute

### 1. Feedback on design

At this stage, the most useful contribution is often **feedback on the scope and design** rather than code. If you have opinions on:

- which statistical methods should be prioritized,
- how the configuration schema should look,
- what output formats matter most for your workflow,
- or whether a specific design decision fits (or conflicts with) your research practice,

please open a **Discussion** or an **Issue** labelled `design-feedback`.

### 2. Bug reports

If you encounter unexpected behaviour, please open an issue with the following:

- A minimal, reproducible example (code, configuration, and a small synthetic dataset if possible).
- The expected behaviour and the observed behaviour.
- Your environment: operating system, Python version, and versions of `pystatkit` and key dependencies (`pingouin`, `pandas`, `statsmodels`).
- The full traceback, if applicable.

Please avoid submitting real participant data with bug reports. Synthetic or anonymized examples are strongly preferred.

### 3. Feature requests

Feature requests are welcome. Before opening one, please search existing issues to avoid duplicates. A useful feature request includes:

- The research scenario motivating the feature.
- The statistical method or output involved, with a reference where appropriate.
- An example of how the feature would be invoked (configuration snippet or API sketch).

### 4. Documentation

Documentation contributions — clarifications, examples, corrected typos, translations — are very welcome and can be submitted via pull request. Documentation changes do not require prior discussion in an issue.

### 5. Code contributions

Code contributions are welcome once the initial API stabilizes. Until the first tagged release, please open an issue to discuss proposed changes before submitting a pull request, to avoid duplicated effort while the design is still in flux.

---

## Development Setup

*These instructions will evolve as the project matures.*

```bash
# Clone the repository
git clone https://github.com/<your-username>/pystatkit.git
cd pystatkit

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

# Install in editable mode with development dependencies
pip install -e ".[dev]"
```

---

## Coding Conventions

- **Python version**: 3.10 or higher.
- **Style**: [PEP 8](https://peps.python.org/pep-0008/), enforced via `ruff`.
- **Formatting**: `black` with default settings.
- **Type hints**: encouraged for all public functions.
- **Docstrings**: NumPy style, including a brief example where useful.
- **Imports**: organized with `isort` (compatible with `black`).

Before submitting a pull request, please run the linters and formatters locally:

```bash
ruff check .
black --check .
```

---

## Testing

Statistical code is particularly prone to silent errors. Tests are therefore treated as essential rather than optional.

- All new statistical functions must include tests that compare results against a trusted reference implementation (typically `pingouin`, `scipy.stats`, or a published textbook example).
- Tests are written with `pytest` and placed in `tests/`.
- Use the built-in example datasets from `pingouin` or small synthetic fixtures. Do not commit real participant data.

Run the test suite with:

```bash
pytest
```

---

## Pull Request Process

1. **Open an issue first** (until the first stable release) to discuss the change.
2. Create a feature branch off `main`:
   ```bash
   git checkout -b feature/<short-description>
   ```
3. Write clear, focused commits. Conventional commit prefixes are encouraged: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`.
4. Ensure all tests pass and that linters are clean.
5. Update relevant documentation (README, docstrings, examples) as part of the same pull request.
6. Open a pull request against `main`. Describe the change, link the related issue, and note any open questions for reviewers.

Pull requests are reviewed as time permits. Please be patient, and feel free to ping the thread after two weeks if there has been no response.

---

## Statistical Correctness

Because `pystatkit` is used to produce results intended for scientific publication, contributions involving statistical methods are held to a high standard:

- **Cite the method.** Link to the primary source or an authoritative textbook in the docstring.
- **Validate against reference software.** Provide a test comparing output to `pingouin`, `scipy.stats`, R, or another trusted implementation, with tolerance thresholds documented.
- **Document assumptions.** Include which assumptions the method requires and how violations are reported to the user.
- **Never silently choose a method on the user's behalf.** The human-in-the-loop principle is core to the project: the toolkit may *suggest*, but it must not *decide*.

---

## Code of Conduct

Contributors are expected to engage respectfully and constructively. Discriminatory, harassing, or otherwise disrespectful behaviour will not be tolerated. A formal Code of Conduct (adapted from the [Contributor Covenant](https://www.contributor-covenant.org/)) will be added before the first tagged release.

In the meantime, a simple rule applies: treat others as you would like to be treated in a collaborative academic environment.

---

## Questions

For general questions about usage or design, please use **GitHub Discussions** rather than opening an issue. Issues are reserved for actionable bug reports and feature requests.

Thank you for helping make `pystatkit` a useful tool for the research community.

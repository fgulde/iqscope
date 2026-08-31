# iqscope

[![Build & Test](https://img.shields.io/github/actions/workflow/status/fgulde/iq-signal-analyzer/build-test.yml?branch=master&label=Build%20%26%20Test)](https://github.com/fgulde/iq-signal-analyzer/actions/workflows/build-test.yml)
[![Code Coverage](https://img.shields.io/github/actions/workflow/status/fgulde/iq-signal-analyzer/coverage.yml?branch=master&label=Code%20Coverage)](https://github.com/fgulde/iq-signal-analyzer/actions/workflows/coverage.yml)
[![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![codecov](https://codecov.io/gh/fgulde/iq-signal-analyzer/graph/badge.svg)](https://codecov.io/gh/fgulde/iq-signal-analyzer)
[![Last commit](https://img.shields.io/github/last-commit/fgulde/iq-signal-analyzer)](https://github.com/fgulde/iq-signal-analyzer/commits/master)
[![License](https://img.shields.io/github/license/fgulde/iq-signal-analyzer)](LICENSE)

Command-line tool for analyzing and demodulating IQ recordings (complex
baseband) as produced by a software-defined radio or a spectrum analyzer.

```
IQ file  →  Spectral analysis  →  Signal detection  →  Channel filtering  →  Demodulation
             (FFT / PSD)          (center freq,          (FIR + decimation)   (FM / AM → WAV)
                                    BW, SNR)
```

Given a raw IQ capture, it produces spectrum/spectrogram plots, a report of
the detected signals (center frequency, bandwidth, SNR), and a demodulated `.wav` file.

## Current Status

🚧 **Early stage — project scaffold only, no signal-processing functionality yet.**

- [x] Phase 0 — Project scaffold (`pyproject.toml`, tooling, CI, module skeleton)
- [ ] Phase 1 — IQ reader
- [ ] Phase 2 — Synthetic signal generator
- [ ] Phase 3 — Spectral analysis
- [ ] Phase 4 — Signal detection & parameter estimation
- [ ] Phase 5 — Filter design & channel selection
- [ ] Phase 6 — Demodulation
- [ ] Phase 7 — CLI, plots & documentation

## Tech Stack

- **Language:** Python 3.13
- **Package Manager:** uv
- **Build backend:** hatchling
- **Libraries:**
  - **Numerics:** NumPy, SciPy
  - **Plotting:** Matplotlib
  - **CLI:** Typer
  - **Testing:** pytest, pytest-cov, Hypothesis
- **Linting, formatting:** ruff
- **Type checking:** mypy (`--strict`)
- **Git hooks:** pre-commit
- **Task runner:** [just](https://github.com/casey/just)
- **CI:** GitHub Actions

## Quick Start

```bash
git clone https://github.com/fgulde/iq-signal-analyzer.git
cd iq-signal-analyzer

just setup
```

Run the quality gates locally (mirrors the CI workflows):

```bash
just lint        # ruff check + format --check
just typecheck    # mypy --strict
just test          # pytest + coverage
just check          # lint + typecheck + test
```

`just --list` shows every available recipe. Without `just`, the equivalent
`uv run ...` commands work too — see the [justfile](justfile).

The CLI entry point (`iqscope`) exists but has no commands wired up yet —
that lands in Phase 7.

## Architecture

**Functional core, imperative shell.**

- The **core** (spectral analysis, detection, filtering, demodulation) is
  pure functions: NumPy arrays in, NumPy arrays or value objects out. No file
  I/O, no logging of results, no side effects, no global state.
- The **shell** (CLI, file access, plot output) is thin and contains no
  domain logic — it reads input, calls into the core, writes output.

Dependencies point inward: the core knows nothing about the CLI or file
formats. Where a core component needs something from the outside (e.g. a
source of samples), that's expressed via a `typing.Protocol`, not a concrete
type.

## Project Structure

```
src/iqscope/
├── types.py               # shared type aliases (IQArray, RealArray), units
├── errors.py               # exception hierarchy
├── io/                      # raw formats → complex64, sample-rate/metadata
├── synth/                   # synthetic signal generator (ground truth for tests)
├── spectral/                # window functions, FFT/PSD, spectrogram
├── detect/                  # noise floor, peak detection, parameter estimation
├── dsp/                      # FIR filter design, mixing, decimation
├── demod/                    # FM / AM demodulation
├── plotting/                 # Matplotlib output (presentation only)
└── cli.py                    # thin CLI adapter

tests/
├── unit/                     # per-module unit tests
├── property/                  # Hypothesis-based invariant tests
└── integration/                # full pipeline: generator → analysis → result
```

## Testing Strategy

Three layers, all run via `pytest`:

1. **Unit tests** — individual functions against analytically known results
   (e.g. an FFT of a pure sine must show a single peak at the expected bin).
2. **Property tests** ([Hypothesis](https://hypothesis.readthedocs.io/)) —
   invariants over randomly generated inputs (Parseval's theorem, linearity
   of the spectrum, decimation-by-1 is the identity, a FIR low-pass can't
   increase signal energy).
3. **Integration tests against ground truth** — the synthetic generator
   produces a signal with a known SNR / frequency offset / bandwidth, and the
   estimate from the analysis pipeline is checked against that known value.

## License

MIT — see [LICENSE](LICENSE).

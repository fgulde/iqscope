"""Thin CLI adapter, no domain logic."""

import typer

__all__ = ["app"]

app = typer.Typer(help="IQ Signal Analyzer: analysis and demodulation of IQ recordings.")
"""Typer app behind the ``iqscope`` console script."""


if __name__ == "__main__":
    app()

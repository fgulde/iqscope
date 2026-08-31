"""Thin CLI adapter layer — no domain logic."""

import typer

__all__ = ["app"]

app = typer.Typer(help="IQ Signal Analyzer — analysis and demodulation of IQ recordings.")


if __name__ == "__main__":
    app()

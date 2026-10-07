"""Commandes de démarrage et d'arrêt de PCWEB."""

from __future__ import annotations

import webbrowser

import typer

from perfcomparatorweb import __version__, process_manager

app = typer.Typer(no_args_is_help=True, help="Interface Web locale de PerfComparator.")


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"PerfComparator Web {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Affiche la version installée.",
    ),
) -> None:
    """Commandes locales du serveur PCWEB."""


@app.command("start")
def start(no_open_browser: bool = typer.Option(False, "--no-open-browser")) -> None:
    """Démarre PCWEB si PCE est disponible."""
    try:
        state = process_manager.start()
    except RuntimeError as error:
        typer.secho(str(error), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from error
    typer.echo(f"PCWEB est disponible sur {state['url']}")
    if not no_open_browser:
        webbrowser.open(str(state["url"]))


@app.command("stop")
def stop() -> None:
    """Arrête PCWEB proprement."""
    try:
        stopped = process_manager.stop()
    except RuntimeError as error:
        typer.secho(str(error), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from error
    typer.echo("PCWEB est arrêté." if stopped else "PCWEB n'était pas démarré.")


@app.command("status")
def status() -> None:
    """Affiche l'état de PCWEB."""
    state = process_manager.status()
    if state:
        typer.echo(f"PCWEB fonctionne sur {state['url']} (PID {state['pid']}).")
    else:
        typer.echo("PCWEB est arrêté.")


if __name__ == "__main__":
    app()

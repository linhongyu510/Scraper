"""Command-line interface."""

import typer

app = typer.Typer(help="Collect and analyze public web data.")
collect_app = typer.Typer(help="Collect records from a source.")
analyze_app = typer.Typer(help="Analyze local records.")
app.add_typer(collect_app, name="collect")
app.add_typer(analyze_app, name="analyze")

from __future__ import annotations

from pathlib import Path

import httpx
from bs4 import BeautifulSoup
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import typer

from collector.utils.http_client import request_with_retries
from collector.utils.shared import DEFAULT_NAMES_FILE, REQUEST_TIMEOUT_SECONDS

console = Console()

app = typer.Typer()


SIMPLE_INDEX_HTML_ACCEPT = "application/vnd.pypi.simple.v1+html"


@app.command()
def fetch_html(
        index: str = "https://pypi.org/",
        route: str = "/simple/",
        output: Path = DEFAULT_NAMES_FILE,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    console.print(Panel.fit(
        f"[bold cyan]Index[/bold cyan]  {index}\n"
        f"[bold cyan]Route[/bold cyan]  {route}\n"
        f"[bold cyan]Output[/bold cyan] {output}",
        title="[bold]fetch-html[/bold]", border_style="cyan",
    ))

    with (console.status("[cyan]Fetching package index (HTML)...", spinner="dots"),
          httpx.Client(verify=False, timeout=REQUEST_TIMEOUT_SECONDS) as client):
        req_url = f"{index}{route}"
        headers = {"Accept": SIMPLE_INDEX_HTML_ACCEPT}

        try:
            response = request_with_retries(
                client, "GET", req_url, headers=headers, log=console.log)
            console.log(response.request.url)
        except Exception as e:
            console.log(f"[red]Error fetching {req_url}: {e}[/red]")
            return

        soup = BeautifulSoup(response.text, "html.parser")
        names = [a.get_text(strip=True)
                 for a in soup.find_all("a") if a.get_text(strip=True)]

    with output.open("w", encoding="utf-8") as file:
        file.writelines(f"{name}\n" for name in names)

    summary = Table(title="fetch-html summary",
                    show_header=False, border_style="green")
    summary.add_column(style="bold cyan")
    summary.add_column()
    summary.add_row("Names written", str(len(names)))
    summary.add_row("Output", str(output))
    console.print(summary)

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.progress import BarColumn, MofNCompleteColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.table import Table
from sqlmodel import SQLModel, Session, create_engine
from typer import BadParameter, Typer

from shared.models import set_last_updated

from collector.utils.shared import DEFAULT_DB_URL, DEFAULT_NAMES_FILE, chunked, count_names, iter_name_file
from collector.utils.storage import persist_name_chunk

console = Console()

app = Typer()

@app.command()
def names(
    index: str = "https://pypi.org",
    names_file: Path = DEFAULT_NAMES_FILE,
    db: str = DEFAULT_DB_URL,
    self_hosted: bool = False,
    chunk_size: int = 2000,
) -> None:

    if not names_file.exists():
        raise BadParameter(f"Names file does not exist: {names_file}")

    engine = create_engine(db, echo=False)
    SQLModel.metadata.create_all(engine)

    with console.status("[cyan]Counting names...", spinner="dots"):
        total_expected = count_names(names_file)

    console.print(Panel.fit(
        f"[bold cyan]Index[/bold cyan]       {index}\n"
        f"[bold cyan]Names file[/bold cyan]  {names_file}\n"
        f"[bold cyan]Total names[/bold cyan] {total_expected}\n"
        f"[bold cyan]Chunk size[/bold cyan]  {chunk_size}\n"
        f"[bold cyan]Self hosted[/bold cyan] {self_hosted}",
        title="[bold]names[/bold]", border_style="cyan",
    ))
    total_names = total_chunks = 0
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TextColumn("[progress.percentage]{task.percentage:>5.1f}%"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
    )
    with progress, Session(engine) as session:
        task_id = progress.add_task("Persisting names", total=total_expected)

        for chunk in chunked(iter_name_file(names_file), chunk_size):
            persist_name_chunk(session, index, self_hosted, chunk)
            total_names += len(chunk)
            total_chunks += 1
            progress.update(task_id, advance=len(chunk))

        set_last_updated(session)

    summary = Table(title="names summary", show_header=False, border_style="green")
    summary.add_column(style="bold cyan")
    summary.add_column()
    summary.add_row("Names processed", str(total_names))
    summary.add_row("Chunks", str(total_chunks))
    console.print(summary)

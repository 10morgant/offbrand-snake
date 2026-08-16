from __future__ import annotations

import asyncio
from pathlib import Path

import httpx
from rich.console import Console
from rich.progress import BarColumn, MofNCompleteColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.table import Table
from sqlmodel import SQLModel, Session, create_engine, select
from typer import BadParameter, Typer

from shared.models import Package, PackageVersion, set_last_updated

from collector.utils.pypi import fetch_package_metadata
from collector.utils.shared import DEFAULT_DB_URL, DEFAULT_NAMES_FILE, PackagePayload, REQUEST_TIMEOUT_SECONDS, count_names, iter_name_file
from collector.utils.storage import persist_package_payload_batch

console = Console()

app = Typer()

def load_processed_packages(session: Session, registry: str, self_hosted: bool) -> frozenset[str]:
    stmt = (
        select(Package.name)
        .join(PackageVersion, PackageVersion.package_id == Package.id)  # type: ignore[arg-type]
        .where(Package.src_registry == registry, Package.self_hosted == self_hosted)
        .distinct()
    )
    return frozenset(session.exec(stmt).all())


@app.command()
def process(
    index: str = "https://pypi.org",
    names_file: Path = DEFAULT_NAMES_FILE,
    db: str = DEFAULT_DB_URL,
    self_hosted: bool = False,
    downloaders: int = 30,
    db_batch_size: int = 200,
    skip_existing: bool = False,
) -> None:
    if not names_file.exists():
        raise BadParameter(f"Names file does not exist: {names_file}")
    asyncio.run(process_async(index, names_file, db, self_hosted, downloaders, db_batch_size, skip_existing))


async def process_async(
    index: str,
    names_file: Path,
    db: str,
    self_hosted: bool,
    downloaders: int,
    db_batch_size: int,
    skip_existing: bool = False,
) -> None:
    engine = create_engine(db, echo=False)
    SQLModel.metadata.create_all(engine)
    with console.status("[cyan]Counting names...", spinner="dots"):
        total_expected = count_names(names_file)

    # packages we already have at least one version for; PyPI returns all versions of a
    # package in a single request, so skip-existing operates per-package rather than per-version
    processed_packages: frozenset[str] = frozenset()
    if skip_existing:
        with console.status("[cyan]Loading processed packages from DB...", spinner="dots"), Session(engine) as session:
            processed_packages = load_processed_packages(session, index, self_hosted)
        console.log(f"[cyan]skip-existing[/cyan] loaded {len(processed_packages)} packages already processed")

    console.print(Panel.fit(
        f"[bold cyan]Index[/bold cyan]         {index}\n"
        f"[bold cyan]Names file[/bold cyan]    {names_file}\n"
        f"[bold cyan]Total names[/bold cyan]   {total_expected}\n"
        f"[bold cyan]Downloaders[/bold cyan]   {downloaders}\n"
        f"[bold cyan]DB batch size[/bold cyan] {db_batch_size}\n"
        f"[bold cyan]Self hosted[/bold cyan]   {self_hosted}\n"
        f"[bold cyan]Skip existing[/bold cyan] {skip_existing}",
        title="[bold]process[/bold]", border_style="cyan",
    ))

    name_queue: asyncio.Queue[str | None] = asyncio.Queue(maxsize=downloaders * 4)
    db_queue: asyncio.Queue[PackagePayload | None] = asyncio.Queue(maxsize=downloaders * 8)
    stats = {"queued": 0, "downloaded": 0, "failed": 0, "processed_versions": 0, "db_batches": 0, "db_records": 0, "skipped_packages": 0}
    batch_versions = {"discovered": 0, "processed": 0}
    # printing directly while the Progress live display is active corrupts its rendering,
    # so events are buffered here and flushed to the console after the display closes
    log_messages: list[str] = []

    def buffer_log(message: str) -> None:
        log_messages.append(message)

    progress = Progress(
        SpinnerColumn(), TextColumn("[bold blue]{task.description}"), BarColumn(),
        MofNCompleteColumn(), TextColumn("[progress.percentage]{task.percentage:>5.1f}%"),
        TextColumn("{task.fields[info]}"), TimeElapsedColumn(), TimeRemainingColumn(), console=console,
    )
    package_task = progress.add_task("Packages", total=total_expected, info="")
    version_task = progress.add_task("New versions (batch)", total=0, info="")

    def refresh_task() -> None:
        progress.update(package_task, info=f"ok=[green]{stats['downloaded']}[/green] fail=[red]{stats['failed']}[/red] batches=[cyan]{stats['db_batches']}[/cyan]")
        progress.update(version_task, info=f"total=[magenta]{stats['processed_versions']}[/magenta] skipped=[yellow]{stats['skipped_packages']}[/yellow]")

    def reset_version_bar() -> None:
        in_flight = max(batch_versions["discovered"] - batch_versions["processed"], 0)
        batch_versions["discovered"], batch_versions["processed"] = in_flight, 0
        progress.reset(version_task, total=in_flight, completed=0, info="")
        refresh_task()

    def on_versions_discovered(count: int) -> None:
        batch_versions["discovered"] += count
        progress.update(version_task, total=batch_versions["discovered"])

    def on_version_processed() -> None:
        batch_versions["processed"] += 1
        stats["processed_versions"] += 1
        progress.advance(version_task, 1)
        refresh_task()

    async def producer() -> None:
        for name in iter_name_file(names_file):
            await name_queue.put(name)
            stats["queued"] += 1
        for _ in range(downloaders):
            await name_queue.put(None)

    async def downloader(worker_id: int, client: httpx.AsyncClient) -> None:
        while True:
            item = await name_queue.get()
            if item is None:
                name_queue.task_done()
                break
            if skip_existing and item in processed_packages:
                stats["skipped_packages"] += 1
                progress.update(package_task, advance=1)
                refresh_task()
                name_queue.task_done()
                continue
            try:
                payload, _ = await fetch_package_metadata(client, index, item, frozenset(), on_versions_discovered, on_version_processed, log=buffer_log)
                if payload is not None:
                    await db_queue.put(payload)
                stats["downloaded"] += 1
            except Exception as exc:
                stats["failed"] += 1
                buffer_log(f"[red]worker={worker_id} failed[/red] package={item} ")#err={exc}")
            finally:
                progress.update(package_task, advance=1)
                refresh_task()
                name_queue.task_done()

    def flush_payloads(session: Session, payloads: list[PackagePayload]) -> int:
        if not payloads:
            return 0
        return persist_package_payload_batch(session, index, self_hosted, payloads)[1]

    async def db_worker() -> None:
        batch: list[PackagePayload] = []
        with Session(engine) as session:
            while True:
                try:
                    item = await asyncio.wait_for(db_queue.get(), timeout=2.0)
                except TimeoutError:
                    if batch:
                        stats["db_records"] += flush_payloads(session, batch)
                        stats["db_batches"] += 1
                        reset_version_bar()
                        batch = []
                    continue
                if item is None:
                    db_queue.task_done()
                    if batch:
                        stats["db_records"] += flush_payloads(session, batch)
                        stats["db_batches"] += 1
                        reset_version_bar()
                    set_last_updated(session)
                    break
                batch.append(item)
                db_queue.task_done()
                if len(batch) >= db_batch_size:
                    stats["db_records"] += flush_payloads(session, batch)
                    stats["db_batches"] += 1
                    reset_version_bar()
                    batch = []

    with progress:
        async with httpx.AsyncClient(verify=False, timeout=REQUEST_TIMEOUT_SECONDS) as client:
            producer_task = asyncio.create_task(producer())
            db_task = asyncio.create_task(db_worker())
            downloader_tasks = [asyncio.create_task(downloader(worker_index + 1, client)) for worker_index in range(downloaders)]
            await producer_task
            await name_queue.join()
            await asyncio.gather(*downloader_tasks)
            await db_queue.put(None)
            await db_queue.join()
            await db_task

    for message in log_messages:
        console.log(message)

    summary = Table(title="process summary", show_header=False, border_style="green")
    summary.add_column(style="bold cyan")
    summary.add_column()
    summary.add_row("Queued", str(stats["queued"]))
    summary.add_row("Downloaded", f"[green]{stats['downloaded']}[/green]")
    summary.add_row("Failed", f"[red]{stats['failed']}[/red]")
    summary.add_row("DB batches", str(stats["db_batches"]))
    summary.add_row("Versions changed", str(stats["db_records"]))
    summary.add_row("Packages skipped (existing)", f"[yellow]{stats['skipped_packages']}[/yellow]")
    console.print(summary)



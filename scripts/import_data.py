#!/usr/bin/env python
"""
CLI commands for importing data from CSV/JSON files.

Usage:
    python scripts/import_data.py --help
    python scripts/import_data.py import-customers data/customers.csv --tenant-id acme-corp
    python scripts/import_data.py import-invoices data/invoices.json --tenant-id acme-corp --dry-run
    python scripts/import_data.py import-status <job-id>
    python scripts/import_data.py list-jobs --status completed
"""

import asyncio
import json
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.dotmac.platform.data_import import DataImportService, ImportJobStatus, ImportJobType
from src.dotmac.platform.database import get_db_session, init_db

app = typer.Typer(help="Data import CLI for DotMac Platform Services")
console = Console()


@app.command()
def import_customers(
    file_path: Path = typer.Argument(..., help="Path to CSV or JSON file containing customer data"),
    tenant_id: str = typer.Option(..., "--tenant-id", "-t", help="Tenant ID for the import"),
    batch_size: int = typer.Option(
        100, "--batch-size", "-b", help="Number of records to process at once"
    ),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Validate data without persisting"),
    user_id: str | None = typer.Option(
        None, "--user-id", "-u", help="User ID initiating the import"
    ),
    async_mode: bool = typer.Option(
        False, "--async", "-a", help="Process import asynchronously using Celery"
    ),
):
    """Import customers from CSV or JSON file."""
    if not file_path.exists():
        console.print(f"[red]Error: File {file_path} not found[/red]")
        raise typer.Exit(1)

    file_ext = file_path.suffix.lower()
    if file_ext not in [".csv", ".json"]:
        console.print("[red]Error: Only CSV and JSON files are supported[/red]")
        raise typer.Exit(1)

    console.print(f"[cyan]Importing customers from {file_path}[/cyan]")
    if dry_run:
        console.print("[yellow]DRY RUN MODE - No data will be persisted[/yellow]")

    asyncio.run(_import_customers(file_path, tenant_id, batch_size, dry_run, user_id, async_mode))


async def _import_customers(
    file_path: Path,
    tenant_id: str,
    batch_size: int,
    dry_run: bool,
    user_id: str | None,
    async_mode: bool = False,
):
    """Async function to import customers."""
    await init_db()

    async with get_db_session() as session:
        service = DataImportService(session)

        try:
            if file_path.suffix.lower() == ".csv":
                with open(file_path, "rb") as f:
                    result = await service.import_customers_csv(
                        f,
                        tenant_id=tenant_id,
                        user_id=user_id,
                        batch_size=batch_size,
                        dry_run=dry_run,
                        use_celery=async_mode,
                    )
            else:  # JSON
                with open(file_path) as f:
                    data = json.load(f)
                    if not isinstance(data, list):
                        console.print(
                            "[red]Error: JSON file must contain an array of customer records[/red]"
                        )
                        raise typer.Exit(1)

                    result = await service.import_customers_json(
                        data,
                        tenant_id=tenant_id,
                        user_id=user_id,
                        batch_size=batch_size,
                        dry_run=dry_run,
                        use_celery=async_mode,
                    )

            # Display results
            _display_import_result(result)

        except Exception as e:
            console.print(f"[red]Import failed: {str(e)}[/red]")
            raise typer.Exit(1)


@app.command()
def import_invoices(
    file_path: Path = typer.Argument(..., help="Path to CSV or JSON file containing invoice data"),
    tenant_id: str = typer.Option(..., "--tenant-id", "-t", help="Tenant ID for the import"),
    batch_size: int = typer.Option(
        100, "--batch-size", "-b", help="Number of records to process at once"
    ),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Validate data without persisting"),
    user_id: str | None = typer.Option(
        None, "--user-id", "-u", help="User ID initiating the import"
    ),
    async_mode: bool = typer.Option(
        False, "--async", "-a", help="Process import asynchronously using Celery"
    ),
):
    """Import invoices from CSV or JSON file."""
    if not file_path.exists():
        console.print(f"[red]Error: File {file_path} not found[/red]")
        raise typer.Exit(1)

    console.print(f"[cyan]Importing invoices from {file_path}[/cyan]")
    if dry_run:
        console.print("[yellow]DRY RUN MODE - No data will be persisted[/yellow]")

    asyncio.run(_import_invoices(file_path, tenant_id, batch_size, dry_run, user_id, async_mode))


async def _import_invoices(
    file_path: Path,
    tenant_id: str,
    batch_size: int,
    dry_run: bool,
    user_id: str | None,
    async_mode: bool = False,
):
    """Async function to import invoices."""
    await init_db()

    async with get_db_session() as session:
        service = DataImportService(session)

        try:
            if file_path.suffix.lower() == ".csv":
                with open(file_path, "rb") as f:
                    result = await service.import_invoices_csv(
                        f,
                        tenant_id=tenant_id,
                        user_id=user_id,
                        batch_size=batch_size,
                        dry_run=dry_run,
                        use_celery=async_mode,
                    )
            else:
                console.print("[yellow]Invoice JSON import not yet implemented[/yellow]")
                return

            _display_import_result(result)

        except Exception as e:
            console.print(f"[red]Import failed: {str(e)}[/red]")
            raise typer.Exit(1)


@app.command()
def import_bulk(
    config_file: Path = typer.Argument(
        ..., help="Path to JSON configuration file for bulk imports"
    ),
    tenant_id: str = typer.Option(..., "--tenant-id", "-t", help="Tenant ID for the import"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Validate data without persisting"),
):
    """
    Perform bulk imports based on configuration file.

    Config file format:
    {
        "imports": [
            {
                "type": "customers",
                "file": "data/customers.csv",
                "batch_size": 100
            },
            {
                "type": "invoices",
                "file": "data/invoices.csv",
                "batch_size": 50
            }
        ]
    }
    """
    if not config_file.exists():
        console.print(f"[red]Error: Config file {config_file} not found[/red]")
        raise typer.Exit(1)

    with open(config_file) as f:
        config = json.load(f)

    console.print(f"[cyan]Starting bulk import with {len(config['imports'])} files[/cyan]")

    for import_config in config["imports"]:
        file_path = Path(import_config["file"])
        import_type = import_config["type"]
        batch_size = import_config.get("batch_size", 100)

        console.print(f"\n[blue]Importing {import_type} from {file_path}[/blue]")

        if import_type == "customers":
            import_customers(
                file_path=file_path,
                tenant_id=tenant_id,
                batch_size=batch_size,
                dry_run=dry_run,
                user_id=None,
            )
        elif import_type == "invoices":
            import_invoices(
                file_path=file_path,
                tenant_id=tenant_id,
                batch_size=batch_size,
                dry_run=dry_run,
                user_id=None,
            )
        else:
            console.print(f"[yellow]Unknown import type: {import_type}[/yellow]")


@app.command()
def import_status(
    job_id: str = typer.Argument(..., help="Import job ID to check status"),
    show_failures: bool = typer.Option(False, "--show-failures", "-f", help="Show failed records"),
):
    """Check the status of an import job."""
    asyncio.run(_check_import_status(job_id, show_failures))


async def _check_import_status(job_id: str, show_failures: bool):
    """Async function to check import status."""
    await init_db()

    async with get_db_session() as session:
        service = DataImportService(session)

        try:
            # Get job details
            from sqlalchemy import select

            from src.dotmac.platform.data_import.models import ImportJob

            result = await session.execute(select(ImportJob).where(ImportJob.id == job_id))
            job = result.scalar_one_or_none()

            if not job:
                console.print(f"[red]Job {job_id} not found[/red]")
                raise typer.Exit(1)

            # Display job details
            _display_job_details(job)

            # Show failures if requested
            if show_failures and job.failed_records > 0:
                failures = await service.get_import_failures(
                    job_id=job_id, tenant_id=job.tenant_id, limit=20
                )
                _display_import_failures(failures)

        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
            raise typer.Exit(1)


@app.command()
def list_jobs(
    tenant_id: str | None = typer.Option(None, "--tenant-id", "-t", help="Filter by tenant ID"),
    status: str | None = typer.Option(
        None, "--status", "-s", help="Filter by status (pending, in_progress, completed, failed)"
    ),
    job_type: str | None = typer.Option(
        None, "--type", help="Filter by job type (customers, invoices, subscriptions, payments)"
    ),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum number of jobs to display"),
):
    """List import jobs with optional filters."""
    asyncio.run(_list_import_jobs(tenant_id, status, job_type, limit))


async def _list_import_jobs(
    tenant_id: str | None, status: str | None, job_type: str | None, limit: int
):
    """Async function to list import jobs."""
    await init_db()

    async with get_db_session() as session:
        from sqlalchemy import select

        from src.dotmac.platform.data_import.models import ImportJob

        query = select(ImportJob)

        if tenant_id:
            query = query.where(ImportJob.tenant_id == tenant_id)
        if status:
            try:
                status_enum = ImportJobStatus(status)
                query = query.where(ImportJob.status == status_enum)
            except ValueError:
                console.print(f"[red]Invalid status: {status}[/red]")
                raise typer.Exit(1)
        if job_type:
            try:
                type_enum = ImportJobType(job_type)
                query = query.where(ImportJob.job_type == type_enum)
            except ValueError:
                console.print(f"[red]Invalid job type: {job_type}[/red]")
                raise typer.Exit(1)

        query = query.order_by(ImportJob.created_at.desc()).limit(limit)

        result = await session.execute(query)
        jobs = result.scalars().all()

        if not jobs:
            console.print("[yellow]No import jobs found[/yellow]")
            return

        _display_jobs_table(jobs)


def _display_import_result(result):
    """Display import result summary."""
    table = Table(title="Import Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Job ID", result.job_id)
    table.add_row("Total Records", str(result.total_records))
    table.add_row("Successful", str(result.successful_records))
    table.add_row("Failed", str(result.failed_records))
    table.add_row("Success Rate", f"{result.success_rate:.1f}%")

    console.print(table)

    if result.warnings:
        console.print("\n[yellow]Warnings:[/yellow]")
        for warning in result.warnings:
            console.print(f"  • {warning}")

    if result.errors:
        console.print(
            f"\n[red]Errors (showing first {min(10, len(result.errors))} of {len(result.errors)}):[/red]"
        )
        for error in result.errors[:10]:
            if "row_number" in error:
                console.print(f"  Row {error['row_number']}: {error['error']}")
            else:
                console.print(f"  • {error.get('error', str(error))}")


def _display_job_details(job):
    """Display detailed job information."""
    table = Table(title=f"Import Job {str(job.id)}")
    table.add_column("Property", style="cyan")
    table.add_column("Value")

    status_color = {
        ImportJobStatus.COMPLETED: "green",
        ImportJobStatus.FAILED: "red",
        ImportJobStatus.IN_PROGRESS: "yellow",
        ImportJobStatus.PENDING: "white",
        ImportJobStatus.PARTIALLY_COMPLETED: "yellow",
    }.get(job.status, "white")

    table.add_row("Type", job.job_type.value)
    table.add_row("Status", f"[{status_color}]{job.status.value}[/{status_color}]")
    table.add_row("File", job.file_name)
    table.add_row("Total Records", str(job.total_records))
    table.add_row("Processed", str(job.processed_records))
    table.add_row("Successful", str(job.successful_records))
    table.add_row("Failed", str(job.failed_records))
    table.add_row("Progress", f"{job.progress_percentage:.1f}%")
    table.add_row("Success Rate", f"{job.success_rate:.1f}%")

    if job.started_at:
        table.add_row("Started", job.started_at.strftime("%Y-%m-%d %H:%M:%S"))
    if job.completed_at:
        table.add_row("Completed", job.completed_at.strftime("%Y-%m-%d %H:%M:%S"))
    if job.duration_seconds:
        table.add_row("Duration", f"{job.duration_seconds:.1f} seconds")

    if job.error_message:
        table.add_row("Error", f"[red]{job.error_message}[/red]")

    console.print(table)


def _display_jobs_table(jobs):
    """Display jobs in a table format."""
    table = Table(title="Import Jobs")
    table.add_column("Job ID", style="cyan")
    table.add_column("Type")
    table.add_column("Status")
    table.add_column("Total")
    table.add_column("Success")
    table.add_column("Failed")
    table.add_column("Progress")
    table.add_column("Created")

    for job in jobs:
        status_color = {
            ImportJobStatus.COMPLETED: "green",
            ImportJobStatus.FAILED: "red",
            ImportJobStatus.IN_PROGRESS: "yellow",
            ImportJobStatus.PENDING: "white",
            ImportJobStatus.PARTIALLY_COMPLETED: "yellow",
        }.get(job.status, "white")

        table.add_row(
            str(job.id)[:8],
            job.job_type.value,
            f"[{status_color}]{job.status.value}[/{status_color}]",
            str(job.total_records),
            str(job.successful_records),
            str(job.failed_records),
            f"{job.progress_percentage:.0f}%",
            job.created_at.strftime("%Y-%m-%d %H:%M"),
        )

    console.print(table)


def _display_import_failures(failures):
    """Display import failures."""
    console.print("\n[red]Failed Records:[/red]")
    for failure in failures:
        console.print(f"\nRow {failure.row_number}:")
        console.print(f"  Error: {failure.error_message}")
        if failure.field_errors:
            console.print("  Field Errors:")
            for field, error in failure.field_errors.items():
                console.print(f"    • {field}: {error}")


if __name__ == "__main__":
    app()

import asyncio
from typing import Optional
import typer

from portex.scanner import create_scanner

app = typer.Typer(help="PORTEX - Advanced Port Scanner")



@app.command()
def scan(
        target: str = typer.Argument(..., help="Target IP/CIDR/domain"),
        ports: str = typer.Option("80,443", "--ports", "-p", help="Ports to scan"),
        protocol: Optional[str] = typer.Option(None, "--protocol", "-P", help="Protocol (tcp/udp/http/https)"),
        timeout: float = typer.Option(2.0, "--timeout", "-T", help="Timeout in seconds"),
        concurrency: int = typer.Option(100, "--concurrency", "-c", help="Max concurrent connections"),
        thread_pool_size: int = typer.Option(200, "--thread_pool_size", "-tps", help="Max concurrent connections"),
        outfile: str = typer.Option(None, "--outfile", "-o", help="Ports to scan"),
        js: bool = typer.Option(False, "--json", "-j", help="JSON output"),
        jsl: bool = typer.Option(False, "--json", "-j", help="JSON output"),
        quiet: bool = typer.Option(False, "--quiet", "-q", help="Disable output")
):
    """
    Scan target hosts and ports
    """

    async def _scan():
        async with create_scanner(
            protocol=protocol,
            target=target,
            ports=ports,
            timeout=timeout,
            concurrency=concurrency,
            thread_pool_size=thread_pool_size,
            js=js,
            jsl=jsl,
            quiet=quiet,
            outfile=outfile,
        ) as scanner:
            await scanner.cmd_run()


    asyncio.run(_scan())


if __name__ == "__main__":
    app()

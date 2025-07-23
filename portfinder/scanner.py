import asyncio
import ipaddress
import json
from collections.abc import (
    AsyncGenerator,
    Coroutine,
    Generator,
)
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path
from typing import (
    Any,
    Callable,
    Optional,
)

import aiofiles
import structlog

from portfinder.dto import (
    IpVersion,
    Protocol,
    Result,
)
from portfinder.utils import (
    check_http_port,
    check_https_port,
    check_tcp_port,
    check_udp_port,
)


logger = structlog.get_logger()


class Scanner:
    __BANNER = """
╔════════════════════════════════════════════════════════╗
    ██████╗  ██████╗ ██████╗ ████████╗███████╗██╗███╗   ██╗██████╗ ███████╗██████╗ 
    ██╔══██╗██╔═══██╗██╔══██╗╚══██╔══╝██╔════╝██║████╗  ██║██╔══██╗██╔════╝██╔══██╗
    ██████╔╝██║   ██║██████╔╝   ██║   █████╗  ██║██╔██╗ ██║██║  ██║█████╗  ██████╔╝
    ██╔═══╝ ██║   ██║██╔══██╗   ██║   ██╔══╝  ██║██║╚██╗██║██║  ██║██╔══╝  ██╔══██╗
    ██║     ╚██████╔╝██║  ██║   ██║   ██║     ██║██║ ╚████║██████╔╝███████╗██║  ██║
    ╚═╝      ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝     ╚═╝╚═╝  ╚═══╝╚═════╝ ╚══════╝╚═╝  ╚═╝
╚════════════════════════════════════════════════════════╝
    """

    def __init__(
        self,
        target: str,
        ports: str = "80,443,53",
        protocol: Protocol | None = None,
        timeout: float = 3.0,
        concurrency: int = 500,
        thread_pool_size: int = 200,
        outfile: str | None = None,
        js: bool = False,
        jsl: bool = False,
        quiet: bool = False,
    ):
        self.target = target
        self._ports = ports
        self.protocols = (
            [Protocol(protocol)] if protocol else [Protocol.TCP, Protocol.UDP, Protocol.HTTP, Protocol.HTTPS]
        )
        self.timeout = timeout
        self.outfile = outfile
        self.js = js
        self.jsl = jsl
        self.ports = self._parse_ports()
        self.concurrency = concurrency
        self.semaphore = asyncio.Semaphore(concurrency)
        self.thread_pool_size = thread_pool_size
        self.thread_pool = ThreadPoolExecutor(max_workers=thread_pool_size)
        self.quiet = quiet
        self._print_banner()

    def _print_banner(self):
        if not self.quiet:
            logger.info(self.__BANNER)
            logger.info(
                "Target: %s \nPorts: %s\nProtocols: %s\nConcurrency: %s\nThread pool size: %s (1 thread / 1 ip) \n %s",
                self.target,
                self._ports,
                [i.value for i in self.protocols],
                self.concurrency,
                self.thread_pool_size,
                "=" * 70,
            )

    def _parse_ports(self) -> list[int]:
        """
        Prepare ports from command parameters
        :return:
        """
        ports: set[int] = set()
        for port in self._ports.split(","):
            if "-" in port:
                start, end = map(int, port.split("-"))
                ports.update(range(start, end + 1))
            else:
                ports.add(int(port))
        return sorted(ports)

    @property
    def proto_call_mapping(self) -> dict[Protocol, Callable[..., Coroutine[Any, Any, bool]]]:
        return {
            Protocol.TCP: check_tcp_port,
            Protocol.UDP: check_udp_port,
            Protocol.HTTP: check_http_port,
            Protocol.HTTPS: check_https_port,
        }

    async def scan_service(
        self, host: str, port: int, protocols: Optional[list[Protocol]] = None, ip_version: IpVersion = IpVersion.IPV4
    ) -> Optional[Result]:
        """
        Call scan request by special or every protocol item
        and log if self.quiet.
        :param host: port string item
        :param port: port integer item
        :param protocols: any from Protocol
        :param ip_version: any from IpVersion
        :return:
        """
        result = Result(host=host, port=port, ip_version=ip_version, protocols=[])
        for proto in protocols:
            if call := self.proto_call_mapping.get(proto):
                if await call(host, port, self.timeout):
                    result.protocols.append(proto)
                    if not self.quiet:
                        logger.info(result)

        return result if result.protocols else None

    def get_targets(self) -> Generator[str, None, None]:
        """
        Prepare targets IPs by subnet CIDR or simple ip return
        :return:
        """
        for target in self.target.replace(" ", "").split(","):
            if "/" in target:
                try:
                    network = ipaddress.ip_network(target, strict=False)
                    for ip in network.hosts():
                        yield str(ip)
                except ValueError:
                    continue
            else:
                yield target

    async def _scan_host(self, host: str) -> list[Result]:
        """
        Execution scan wrapper request host
        Args:
            host: host string item
        Returns: list[Result]
        """
        ip_version = IpVersion.IPV6 if ":" in host else IpVersion.IPV4
        tasks = [self._scan_wrapper(host, port, ip_version) for port in self.ports if port <= 65535]
        return [r for r in await asyncio.gather(*tasks) if r is not None]

    async def _scan_wrapper(self, host: str, port: int, ip_version: IpVersion) -> Optional[Result]:
        """
        Async loop semaphore run wrapper.
        :param host: host string item
        :param port: port integer item
        :param ip_version:
        :return:
        """
        async with self.semaphore:
            return await self.scan_service(host, port, self.protocols, ip_version)

    async def run(self) -> list[Result]:
        """
        Run the scan with thread and async pool.
        One thread for each host will be created.
        :return: list of Result
        """
        loop = asyncio.get_event_loop()
        scan_lambda: Callable[[str], list[Result]] = lambda h: asyncio.run(self._scan_host(h))

        futures = [loop.run_in_executor(self.thread_pool, scan_lambda, host) for host in self.get_targets()]

        results: list[Result] = []
        for future in asyncio.as_completed(futures):
            host_results = await future
            results.extend(host_results)

        return results

    async def cmd_run(self):
        """
        Wrapper for run scan with result saving
        :return:
        """
        results = await self.run()
        if self.outfile:
            await self._save_results(results)
        if not self.quiet:
            await self._print_results(results)

    async def _print_results(self, results: list[Result]) -> None:
        """
        Return result in stdout
        :param results: list of Result
        :return:
        """
        hosts: dict[str, list[Result]] = dict()
        for res in results:
            if res.host not in hosts:
                hosts[res.host] = []
            hosts[res.host].append(res)

        for host, host_results in hosts.items():
            logger.info("\nResults for %s | %s ports found", host, len(host_results))
            for res in host_results:
                logger.info(str(res))

    async def _save_results(self, results: list[Result]):
        """
        Saves results to a TXT, JSON or JSONL file.
        :param results: list of Result
        :return:
        """
        if self.outfile is not None:
            output_path: Path = Path(self.outfile)

            if not self.js and not self.jsl:
                async with aiofiles.open(output_path.with_suffix(".txt"), "w") as f:
                    for res in results:
                        if res:
                            await f.write(str(res))
            elif self.js:
                async with aiofiles.open(output_path.with_suffix(".json"), "w") as f:
                    await f.write(json.dumps([r.to_dict() for r in results if r], indent=2))
            elif self.jsl:
                async with aiofiles.open(output_path.with_suffix(".jsonl"), "w") as f:
                    for res in results:
                        if res:
                            await f.write(json.dumps(res.to_dict()) + "\n")

    def close(self, wait: bool = True):
        """
        Close the connection to the server
        Args:
            wait: bool default True

        Returns:
        """
        self.thread_pool.shutdown(wait=wait)


@asynccontextmanager
async def create_scanner(**kwargs: dict[str, Any]) -> AsyncGenerator[Scanner, None]:
    scanner: Scanner = Scanner(**kwargs)  # type: ignore[arg-type]
    try:
        yield scanner
    finally:
        scanner.close()

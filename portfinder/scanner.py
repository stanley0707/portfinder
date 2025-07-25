import asyncio
import ipaddress
import sys
from collections.abc import (
    AsyncGenerator,
    Coroutine,
)
from contextlib import suppress
from pathlib import Path
from typing import (
    Any,
    Callable,
    Optional,
)

import structlog

from portfinder.dto import (
    IpVersion,
    Protocol,
    Result,
    ResultFileFormatEnum,
)
from portfinder.utils import (
    check_http_port,
    check_https_port,
    check_tcp_port,
    check_udp_port,
    read_file,
    save_result,
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
        target: str | None = None,
        ports: str = "80,443,53",
        protocol: Protocol | None = None,
        timeout: float = 3.0,
        concurrency: int = 500,
        outfile: str | None = None,
        file: str | None = None,
        js: bool = False,
        jsl: bool = False,
        quiet: bool = False,
        uvloop_disable: bool = False,
    ):
        if not any([target, file]):
            raise ValueError("target or file are required")
        self.target = target
        self._ports = ports
        self.protocols = (
            [Protocol(protocol)] if protocol else [Protocol.TCP, Protocol.UDP, Protocol.HTTP, Protocol.HTTPS]
        )
        self.timeout = timeout
        self.outfile = outfile
        self.input_file = file
        self.js = js
        self.jsl = jsl
        self.ports = self._parse_ports()
        self.concurrency = concurrency
        self.semaphore = asyncio.Semaphore(concurrency)
        self.quiet = quiet
        self.uvloop_disable = uvloop_disable

        self._print_banner()

    async def _ensure_uvloop(self):
        """
        Init uvloop for Darwin or Linux if needed
        Returns:
        """
        if self.uvloop_disable or sys.platform == "win32":
            return
        import uvloop

        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    @property
    def result_format(self) -> ResultFileFormatEnum:
        """
        Result file format by command parameters
        return ResultFileFormatEnum
        """
        if self.js:
            return ResultFileFormatEnum.JSON
        elif self.jsl:
            return ResultFileFormatEnum.JSONL

        return ResultFileFormatEnum.TXT

    @property
    def proto_call_mapping(self) -> dict[Protocol, Callable[..., Coroutine[Any, Any, bool]]]:
        return {
            Protocol.TCP: check_tcp_port,
            Protocol.UDP: check_udp_port,
            Protocol.HTTP: check_http_port,
            Protocol.HTTPS: check_https_port,
        }

    def _print_banner(self):
        if not self.quiet:
            logger.info(self.__BANNER)
            logger.info(
                "\nTarget: %s \nPorts: %s\nProtocols: %s\nConcurrency: %s\n %s",
                self.target or self.input_file,
                self._ports,
                [i.value for i in self.protocols],
                self.concurrency,
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

    async def _process_target(self, target: str) -> AsyncGenerator[str, None]:
        """
        Internal generator for one target processing (IP or CIDR)
        return AsyncGenerator string
        """
        if "/" in target:
            try:
                network = ipaddress.ip_network(target, strict=False)
                for ip in network.hosts():
                    yield str(ip)
                    await asyncio.sleep(0.1)
            except ValueError:
                return
        else:
            yield target
            await asyncio.sleep(0.1)

    async def get_targets(self) -> AsyncGenerator[str, None]:
        """
        Prepare targets IPs by subnet CIDR or simple ip return.
        return AsyncGenerator IP from _process_target wrapper function
        """
        if self.input_file is not None:
            async for line in read_file(Path(self.input_file)):
                for target in line.strip().split(","):
                    async for ip in self._process_target(target):
                        yield ip

        if self.target is not None:
            for target in self.target.replace(" ", "").split(","):
                async for ip in self._process_target(target):
                    yield ip

    async def scan_service(
        self, host: str, port: int, protocols: list[Protocol], ip_version: IpVersion = IpVersion.IPV4
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
                        await logger.ainfo(result)

        return result if result.protocols else None

    async def scan_port(self, host: str, port: int) -> Optional[Result]:
        """
        Call scan request by special or every protocol item
        with semaphore.
        """
        ip_version = IpVersion.IPV6 if ":" in host else IpVersion.IPV4
        try:
            async with self.semaphore:
                return await self.scan_service(host, port, self.protocols, ip_version)
        except asyncio.CancelledError:
            pass

        return None

    async def run(self) -> list[Result]:
        """
        Run asynchronously scan port scan as completed and return result
        """
        await self._ensure_uvloop()
        results: list[Result] = []
        for future in asyncio.as_completed(
            [self.scan_port(host, port) async for host in self.get_targets() for port in self.ports if port <= 65535]
        ):
            if result := await future:
                results.append(result)

        return results

    async def cmd_run(self):
        """
        Wrapper for run scan with result saving and
        suppress exceptions for cancellation, KeyboardInterrupt and any Runtime
        from cli command running
        :return:
        """
        with suppress(asyncio.CancelledError, KeyboardInterrupt, RuntimeError):
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
            await logger.ainfo("\nResults for %s | %s ports found", host, len(host_results))
            for res in host_results:
                await logger.ainfo(str(res))

    async def _save_results(self, results: list[Result]) -> None:
        """
        Saves results to a TXT, JSON or JSONL file.
        :param results: list of Result
        :return:
        """
        if self.outfile is not None:
            output_path: Path = Path(self.outfile)
            await save_result(output_path, self.result_format, results)

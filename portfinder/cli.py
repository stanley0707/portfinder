import argparse
import asyncio

from portfinder.scanner import create_scanner


def parse_args():
    parser = argparse.ArgumentParser(description="PORTFINDER - Advanced Port Scanner")
    parser.add_argument("-t", "--target", required=True, help="Target IP/CIDR/domain (comma-separated)")
    parser.add_argument("-p", "--ports", default="80,443,53", help="Ports to scan (e.g. '1-1000,3389')")
    parser.add_argument("-P", "--protocol", help="Protocol to check (tcp, udp, http, https)")
    parser.add_argument("-T", "--timeout", type=float, default=2.0, help="Timeout in seconds")
    parser.add_argument("-c", "--concurrency", type=int, default=300, help="Maximum concurrent connections per host")
    parser.add_argument("-tps", "--thread-pool-size", type=int, default=200, help="Thread pool size for hosts scanning")
    parser.add_argument("-o", "--outfile", help="Output file path (without extension)")
    parser.add_argument("-j", "--js", action="store_true", help="Output in JSON format")
    parser.add_argument("-jl", "--jsl", action="store_true", help="Output in JSON Lines format")
    parser.add_argument("-q", "--quiet", action="store_true", help="Disable all stdout output")
    return parser.parse_args()


async def main():
    args = parse_args()
    async with create_scanner(**vars(args)) as scanner:
        await scanner.cmd_run()


def run():
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())

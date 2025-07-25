import argparse
import asyncio
import sys

from portfinder.scanner import Scanner


def parse_args():
    parser = argparse.ArgumentParser(description="PORTFINDER - Advanced Port Scanner")
    parser.add_argument("-t", "--target", help="Target IP/CIDR/domain (comma-separated)")
    parser.add_argument("-f", "--file", help="Target IP/CIDR/domain txt file (new-line-separated)")
    parser.add_argument("-p", "--ports", default="80,443,53", help="Ports to scan (e.g. '1-1000,3389')")
    parser.add_argument("-P", "--protocol", help="Protocol to check (tcp, udp, http, https)")
    parser.add_argument("-T", "--timeout", type=float, default=2.0, help="Timeout in seconds")
    parser.add_argument("-c", "--concurrency", type=int, default=1000, help="Maximum concurrent connections per host")
    parser.add_argument("-o", "--outfile", help="Output file path (without extension)")
    parser.add_argument("-j", "--js", action="store_true", help="Output in JSON format")
    parser.add_argument("-jl", "--jsl", action="store_true", help="Output in JSON Lines format")
    parser.add_argument("-q", "--quiet", action="store_true", help="Disable all stdout output")
    parser.add_argument("-u", "--uvloop_disable", action="store_true", help="Disable uvloop")
    return parser.parse_args()  # uvloop_enabled


async def main():
    args = parse_args()
    scanner = Scanner(**vars(args))
    await scanner.cmd_run()


def run():
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, RuntimeError):
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())

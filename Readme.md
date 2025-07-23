# PORTFINDER


Portfinder is a powerful asynchronous port scanner for Python that allows you to quickly scan multiple targets with flexible configuration options.

Features
Scan multiple IPs, CIDR ranges or domains

Custom port ranges support (e.g., 1-1000,3389,8080)

Protocol-specific scanning (TCP, UDP, HTTP, HTTPS)

High performance with async I/O and thread pooling

Multiple output formats (JSON, JSON Lines)

Quiet mode for scripting


### installation as python library
```commandline
pip install portfinder
```
Доступно на [PyPI](https://pypi.org/project/portfinder/)


### run basic scan
```commandline
portfinder -t example.com
```

### advanced scan
```commandline
portfinder -t 192.168.1.1,10.0.0.0/24,example.com -p 1-1024,3389,8080 -P http -T 1.5 -c 500 -tps 300 -o scan_results -j
```

| Argument                | Description                                             |
|-------------------------|---------------------------------------------------------|
| `-t`, `--target`        | Target IP/CIDR/domain (comma-separated) (required)      |
| `-p`, `--ports`         | Ports to scan (default: `80,443,53`)                    |
| `-P`, `--protocol`      | Protocol to check (tcp, udp, http, https)               |
| `-T`, `--timeout`       | Timeout in seconds (default: 2.0)                       |
| `-c`, `--concurrency`   | Maximum concurrent connections per host (default: 300) no more than ~500-1000 on CPU cores |
| `-ips`, `-ip-pool-size` | Thread pool size for hosts scanning (default: 200)      |
| `-o`, `--outfile`       | Output file path (without extension)                    |
| `-j`, `--js`            | Output in JSON format                                   |
| `-jl`, `--jsl`          | Output in JSON Lines format                             |
| `-q`, `--quiet`         | Disable all stdout output                               |

### basic python usage

```python
from portfinder.scanner import Scanner
from portfinder.dto import Protocol, Result

async def run_scan():
    ...
    scanner = Scanner(
        target="0.0.0.0",
        ports="80-23000",
        protocol=Protocol.HTTP,
        timeout=4.0,
        concurrency=400,
        ip_pool_size=200,
    )
    results: list[Result] = await scanner.run()
    ...
```
* `Result` is a active port item (dataclass) with attributes:
  * host: str
  * port: int
  * ip_version: IpVersion
  * protocols: list[Protocol]
* `Protocol` enum:
   * HTTP,
   * HTTPS,
   * TCP,
   * UDP

## output files format:
* txt file
```txt
...
0.0.0.0:21 [ipv4] (tcp)
...
```
* json file
```json
[
  ...
  {
    "host": "0.0.0.0",
    "port": 21,
    "ip_version": "ipv4",
    "protocols": [
      [
        "tcp"
      ]
    ]
  },
...
]
```
* jsonl file
```json lines
...
{"host": "0.0.0.0", "port": 53, "ip_version": "ipv4", "protocols": [["tcp"]]}
...

```
### powered by lynkey.io
License
MIT



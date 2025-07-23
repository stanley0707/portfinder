import asyncio

import aiohttp


async def check_udp_port(host: str, port: int, timeout: float = 1.0) -> bool:
    """
    Asynchronously checks if a UDP port is open on a given host
    with timeout.
    Args:
        host (str): The hostname or IP address to connect to.
        port (int): The UDP port number to check.
        timeout (int): The maximum time (in seconds) to wait for a connection.

    Returns:
        bool: True if the port is open, False otherwise.
    """
    loop = asyncio.get_running_loop()
    result = False

    class Protocol(asyncio.DatagramProtocol):
        def __init__(self):
            self.response_received = asyncio.Event()
            self.transport = None

        def connection_made(self, transport):
            self.transport = transport
            transport.sendto(b"\x00")

        def datagram_received(self, data, addr):
            nonlocal result
            result = True
            self.response_received.set()

        def error_received(self, exc):
            self.response_received.set()

        def connection_lost(self, exc):
            self.response_received.set()

    try:
        transport, protocol = await loop.create_datagram_endpoint(Protocol, remote_addr=(host, port))

        try:
            await asyncio.wait_for(
                protocol.response_received.wait(),
                timeout,
            )
            return result
        except asyncio.TimeoutError:
            return False
        finally:
            transport.close()

    except (OSError, ConnectionRefusedError):
        return False


async def check_tcp_port(host, port, timeout=1) -> bool:
    """
    Asynchronously checks if a TCP port is open on a given host
    with timeout.
    Args:
        host (str): The hostname or IP address to connect to.
        port (int): The TCP port number to check.
        timeout (int): The maximum time (in seconds) to wait for a connection.

    Returns:
        bool: True if the port is open, False otherwise.
    """
    writer = None
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=timeout)
        return True
    except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
        return False
    except Exception as _:
        return False
    finally:
        if writer:
            writer.close()
            await writer.wait_closed()


async def check_http_port(host: str, port: int, ssl: bool = False, timeout: float = 3.0) -> bool:
    """
    Asynchronously checks if a HTTP port is open on a given host
    :param host:
    :param port:
    :param ssl:
    :param timeout:
    :return:
    """
    url = f"http{'s' if ssl else ''}://{host}:{port}"
    try:
        connector = aiohttp.TCPConnector(force_close=True)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(
                url,
                ssl=False,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as resp:
                return resp.status < 500
    except Exception:
        return False


async def check_https_port(host: str, port: int, timeout: float = 3.0) -> bool:
    """
    Asynchronously checks if a HTTPS port is open on a given host
    :param host:
    :param port:
    :param timeout:
    :return:
    """
    return await check_http_port(host, port, ssl=True, timeout=timeout)

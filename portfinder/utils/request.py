import asyncio
import ssl


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
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError, ssl.SSLError):
            return False
        except ConnectionResetError:
            return True
        finally:
            try:
                transport.close()
            except ConnectionResetError:
                return True
            except (ssl.SSLError, asyncio.TimeoutError):
                pass

    except (OSError, ConnectionRefusedError):
        return False
    return True


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
    except (asyncio.TimeoutError, ConnectionRefusedError, OSError, ssl.SSLError):
        return False
    except ConnectionResetError:
        return True
    finally:
        if writer is not None:
            try:
                writer.close()
                await writer.wait_closed()
            except ConnectionResetError:
                return True
            except (ssl.SSLError, asyncio.TimeoutError):
                pass
    return True


async def check_http_port(host: str, port: int, timeout: float = 3.0) -> bool:
    """
    Asynchronously checks if a HTTP port is open on a given host
    :param host:
    :param port:
    :param ssl:
    :param timeout:
    :return:
    """
    writer = None
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout,
        )
        writer.write(b"GET / HTTP/1.1\r\nHost: portfinder_scan\r\n\r\n")
        await asyncio.wait_for(writer.drain(), timeout=timeout)
    except (asyncio.TimeoutError, ConnectionRefusedError, OSError, ssl.SSLError):
        return False
    except ConnectionResetError:
        return True
    finally:
        if writer is not None:
            try:
                writer.close()
                await writer.wait_closed()
            except ConnectionResetError:
                return True
            except (ssl.SSLError, asyncio.TimeoutError):
                pass
    return True


async def check_https_port(host: str, port: int, timeout: float = 3.0) -> bool:
    """
    Asynchronously checks if a HTTPS port is open on a given host
    :param host:
    :param port:
    :param timeout:
    :return:
    """
    writer = None
    try:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port, ssl=ssl_context),
            timeout=timeout,
        )

        writer.write(b"GET / HTTP/1.1\r\nHost: lol\r\n\r\n")
        await asyncio.wait_for(writer.drain(), timeout=timeout)
        return True

    except (asyncio.TimeoutError, ConnectionRefusedError, OSError, ssl.SSLError):
        return False
    except ConnectionResetError:
        return True
    finally:
        if writer is not None:
            try:
                writer.close()
                await writer.wait_closed()
            except ConnectionResetError:
                return True
            except (ssl.SSLError, asyncio.TimeoutError):
                pass
    return True

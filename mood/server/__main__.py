"""Start server and roaming_monster function."""
from ..server import server as srv

port = 1337


async def main(port):
    """Start roaming_monster and asyncio server."""
    srv.task = srv.asyncio.create_task(srv.roaming_monster())
    await srv.asyncio.sleep(0)
    server = await srv.asyncio.start_server(srv.mud, '0.0.0.0', port)
    async with server:
        await server.serve_forever()


def server():
    """Start server."""
    srv.asyncio.run(main(port))

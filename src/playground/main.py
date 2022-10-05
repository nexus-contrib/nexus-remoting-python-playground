import asyncio
import sys
from typing import Awaitable
from .utils import load_extensions

from nexus_extensibility import DataSourceContext, IDataSource, ILogger
from nexus_remoting import RemoteCommunicator


class PlaygroundDataSource(IDataSource):
    
    async def set_context(self, context: DataSourceContext, logger: ILogger) -> None:
        a = load_extensions("playground")

# args
if len(sys.argv) < 3:
    raise Exception("No argument for address and/or port was specified.")

# get address
address = sys.argv[1]

# get port
try:
    port = int(sys.argv[2])
except Exception as ex:
    raise Exception(f"The second command line argument must be a valid port number. Inner error: {str(ex)}")

# run
asyncio.run(RemoteCommunicator(PlaygroundDataSource(), address, port).run())

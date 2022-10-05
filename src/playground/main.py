import asyncio
import sys

from nexus_remoting import RemoteCommunicator

from core import PlaygroundDataSource

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

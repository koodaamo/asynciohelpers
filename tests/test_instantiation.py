import asyncio
import multiprocessing
import signal
import time

from pytest import mark
from asynciohelpers.wamp import WAMPSessionTimeoutError

from .servers import ConnectingAsyncioServer, ReConnectingAsyncioServer
from .servers import ConnectingWAMPService, ReConnectingWAMPService
from .fixtures import with_mock_server, with_delayed_mock_server


test_all = (
   ConnectingAsyncioServer, ReConnectingAsyncioServer,
   ConnectingWAMPService, ReConnectingWAMPService
)


@mark.parametrize('serviceklass', test_all)
def test_01_instantiate_ok(serviceklass):
   "all servers can be instantiated"
   serviceklass()


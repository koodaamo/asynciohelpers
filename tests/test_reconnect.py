import sys, time, asyncio, logging, signal, multiprocessing, inspect
from pytest import raises, mark, fixture

from asynciohelpers.service import AsyncioServiceBase
from asynciohelpers.exceptions import SetupException
from asynciohelpers.testing import get_socket_server

from .fixtures import with_mock_server
from .servers import ReConnectingAsyncioServer, ReConnectingWAMPService
from .config import TEST_HOST, TEST_PORT, logger


tested_services = (ReConnectingAsyncioServer, )


@fixture(scope="module", params=tested_services)
def servicefactory(request):
   "run tests for each server"
   yield request.param
   return


@mark.asyncio(forbid_global_loop=True)
async def test_01_internal_loop_reconnect(servicefactory, event_loop):

   mock = await get_socket_server(event_loop, TEST_HOST, TEST_PORT)

   # mock server started

   server = servicefactory(loop=event_loop)
   await server.start()

   # client started, let things go smooth for a while

   await asyncio.sleep(2, loop=event_loop)

   mock.close()
   await mock.wait_closed()

   # mock closed, client is retrying

   await asyncio.sleep(2, loop=event_loop)

   mock = await get_socket_server(event_loop, TEST_HOST, TEST_PORT)

   # hurrah, client should now be able to reconnect
   await asyncio.sleep(2, loop=event_loop)

   # stop
   await server.stop()
   mock.close()
   await mock.wait_closed()


import sys, time, asyncio, logging, signal, multiprocessing, inspect
from pytest import raises, mark, fixture

from asynciohelpers.service import AsyncioServiceBase
from asynciohelpers.exceptions import SetupException
from asynciohelpers.testing import get_socket_server

from .fixtures import with_mock_server
from .servers import ConnectingAsyncioServer, ReConnectingAsyncioServer
from .servers import ConnectingWAMPService, ReConnectingWAMPService
from .config import TEST_HOST, TEST_PORT, logger


tested_services = (ConnectingAsyncioServer, ReConnectingAsyncioServer, )

#ConnectingWAMPService, ReConnectingWAMPService)


@fixture(scope="module", params=tested_services)
def servicefactory(request):
   "run tests for each server"
   yield request.param
   return



@mark.asyncio(forbid_global_loop=True)
async def test_01_internal_loop_connect(servicefactory, event_loop):

   def start_mock():
      "start a dummy TCP/IP socket server to connect to"
      server_coro = get_socket_server(event_loop, TEST_HOST, TEST_PORT)
      return server_coro

   mock = await start_mock()

   server = servicefactory()
   server.set_loop(event_loop)
   await server.start()
   await server.stop()

   mock.close()


def test_02_external_loop_connect(servicefactory, with_mock_server):

   def connect(factory, evt):
      policy = asyncio.get_event_loop_policy()
      policy.set_event_loop(policy.new_event_loop())
      server = factory()
      signal.signal(signal.SIGTERM, server.stop)

      try:
         server.start()
      except SetupException as exc:
         evt.set()
      except:
         raise Exception("unexpected expetion")

   evt = multiprocessing.Event() # failure flag
   sp = multiprocessing.Process(target=connect, args=(servicefactory, evt))
   time.sleep(0.5)
   sp.start()
   time.sleep(0.1)
   sp.terminate()
   sp.join()
   assert not evt.is_set()




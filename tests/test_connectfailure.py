import sys, time, asyncio, logging, signal, multiprocessing, inspect
from pytest import raises, mark, fixture

from asynciohelpers.service import AsyncioBase
from asynciohelpers.exceptions import SetupException
from asynciohelpers.testing import get_socket_server, get_http_server

from .fixtures import with_mock_server
from .servers import ConnectingAsyncioServer, ConnectingWAMPService
from .config import TEST_HOST, TEST_PORT, logger


tested_services = (ConnectingAsyncioServer, ConnectingWAMPService)


@fixture(scope="module", params=tested_services)
def servicefactory(request):
   "run tests for each server"
   yield request.param
   return


@mark.asyncio(forbid_global_loop=True)
async def test_01_internal_loop_cannotconnect(servicefactory, event_loop):

   server = ConnectingAsyncioServer()
   server.set_loop(event_loop)
   with raises(SetupException):
      await server.start()


def test_02_external_loop_cannotconnect(servicefactory):

   def fail(factory, evt):
      policy = asyncio.get_event_loop_policy()
      policy.set_event_loop(policy.new_event_loop())
      server = factory()
      try:
         server.start()
      except SetupException as exc:
         evt.set()
      except:
         raise Exception("unexpected expetion")
      else:
         raise Exception("no exception")

   evt = multiprocessing.Event() # failure flag
   sp = multiprocessing.Process(target=fail, args=(servicefactory, evt))
   sp.start()
   time.sleep(0.5)
   sp.join()
   time.sleep(0.5)

   assert evt.is_set()




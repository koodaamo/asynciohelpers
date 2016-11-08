import os, sys, time, asyncio, logging, signal, multiprocessing, inspect, subprocess
from pytest import raises, mark, fixture

from .fixtures import with_mock_server #, crossbar
from .servers import ConnectingWAMPService, ReConnectingWAMPService
from .config import TEST_HOST, TEST_PORT, logger
from .utils import get_socket_server, get_http_server


tested_services = (ConnectingWAMPService, ReConnectingWAMPService,)


# context manager to start crossbar

def crossbar_router():
   CBCMD = os.environ.get("CROSSBAR")
   assert CBCMD, "Must have environment variable CROSSBAR set to crossbar binary path"
   cdir = os.path.dirname(__file__)
   cbp = subprocess.Popen([CBCMD, "start", "--cbdir", cdir], stdout=subprocess.DEVNULL)
   yield cbp
   cbp.terminate()
   cb.wait()


# asynchronous version

class CrossbarRouter:

   async def __aenter__(self):
      CBCMD = os.environ.get("CROSSBAR")
      assert CBCMD, "Must have environment variable CROSSBAR set to crossbar binary path"
      cdir = os.path.dirname(__file__)
      coro = asyncio.create_subprocess_exec(CBCMD, "start", "--cbdir", cdir, stdout=subprocess.DEVNULL)
      self.cbp = await coro

   async def __aexit__(self, exc_type, exc, tb):
      self.cbp.terminate()
      await self.cbp.wait()


@fixture(scope="module", params=tested_services)
def servicefactory(request):
   "run tests for each server"
   yield request.param
   return


@mark.asyncio(forbid_global_loop=False)
async def test_01_join_realm_reconnect(servicefactory, event_loop):

   loop = event_loop

   server = servicefactory(loop=loop)

   async with CrossbarRouter() as cb:
      print("router starting...")
      await asyncio.sleep(5)
      await server.start()


   # router should now be shut down; start it again and see what happens.
   print("router closed")

   await asyncio.sleep(3)

   async with CrossbarRouter() as cb:
      print("router starting...")
      await asyncio.sleep(5)
      await server.stop()


"""
def test_01_join_realm_reconnect(servicefactory):

   loop = asyncio.get_event_loop()

   with CrossbarRouter() as cb:

      # give router some time to start
      loop.run_until_complete(asyncio.sleep(3))

      # start server
      server = servicefactory(loop=loop)
      loop.run_until_complete(server.start())

      loop.run_until_complete(asyncio.sleep(3))

   # router should now be shut down; start it again and see what happens.

   with CrossbarRouter() as cb:

      loop.run_until_complete(asyncio.sleep(3))

      # restart router
      #cb2 = subprocess.Popen([CBCMD, "start", "--cbdir", ], stdout=subprocess.DEVNULL)

      # let server reconnect, then shut everything down after that
      loop.run_until_complete(asyncio.sleep(4))

      loop.run_until_complete(server.stop())
"""

"""

For some reason, this does not work:

@mark.asyncio(forbid_global_loop=True)
async def test_01_join_realm(servicefactory, event_loop): # crossbar

   server = servicefactory(loop=event_loop)
   await server.start()
   await asyncio.sleep(6, loop=event_loop)
   await server.stop()

(the component never connects; maybe the default global loop is still used somewhere)

"""

import os, sys, time, asyncio, logging, signal, multiprocessing, inspect, subprocess
from concurrent.futures import ProcessPoolExecutor

from pytest import raises, mark, fixture

from asynciohelpers.testing import crossbar_router, CrossbarRouter

from .fixtures import with_mock_server, crossbar_router_running
from .servers import ConnectingWAMPService, ReConnectingWAMPService
from .config import TEST_HOST, TEST_PORT, logger


tested_services = (ConnectingWAMPService, ReConnectingWAMPService,)


@fixture(scope="module", params=tested_services)
def servicefactory(request):
   "run tests for each server"
   yield request.param
   return


def test_01_join_realm(servicefactory, crossbar_router_running, event_loop):
   server = servicefactory()
   server.set_loop(event_loop)
   event_loop.run_until_complete(server.start())
   event_loop.run_until_complete(server.stop())
   remaining = asyncio.Task.all_tasks(loop=event_loop)
   event_loop.run_until_complete(asyncio.gather(*remaining))


def test_02_forked_join_realm(servicefactory):

   def run_server():
      loop = asyncio.new_event_loop()
      asyncio.set_event_loop(loop)
      server = servicefactory()
      server.start()

   s = multiprocessing.Process(target=run_server)

   with crossbar_router() as cb:
      s.start()
      time.sleep(2)
      s.terminate()
      s.join()

   #s_coro = loop.run_in_executor(ProcessPoolExecutor(), server.start)
   #task = asyncio.ensure_future(s_coro, loop=loop)
   #loop.run_until_complete(task)


@mark.asyncio
async def test_03_asyncio_join_realm(servicefactory, event_loop, crossbar_router_running):

   server = servicefactory()
   server.set_loop(event_loop)
   await server.start()
   await asyncio.sleep(6, loop=event_loop)
   await server.stop()


@mark.asyncio
async def test_031_asyncio_join_realm(servicefactory, event_loop):

   server = servicefactory()
   server.set_loop(event_loop)

   async with CrossbarRouter(event_loop) as cb:
      await server.start()
      await server.stop()

   await asyncio.sleep(1, loop=event_loop)


@mark.asyncio
async def test_04_rejoin_realm(servicefactory, event_loop):

   server = servicefactory()
   server.set_loop(event_loop)

   async with CrossbarRouter(event_loop) as cb:
      await server.start()

   print("-------------\n router stopped, waiting a while...\n-----------")
   await asyncio.sleep(1, loop=event_loop)

   async with CrossbarRouter(event_loop) as cb:
      await asyncio.sleep(2, loop=event_loop)
      await server.stop()

   await asyncio.sleep(1, loop=event_loop)

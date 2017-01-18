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
def test_01_connect(serviceklass, with_mock_server):

   def connect(factory, evt):
      policy = asyncio.get_event_loop_policy()
      policy.set_event_loop(policy.new_event_loop())
      server = factory()
      signal.signal(signal.SIGTERM, server.stop)

      try:
         server.start()
      except WAMPSessionTimeoutError as exc:
         pass
      except Exception as exc:
         print(exc)
         evt.set()


   evt = multiprocessing.Event() # failure flag
   sp = multiprocessing.Process(target=connect, args=(serviceklass, evt))
   sp.start()
   time.sleep(3)
   sp.terminate()
   sp.join()
   assert not evt.is_set()


@mark.parametrize('serviceklass', test_all)
def test_02_connect_fail(serviceklass):

   def fail(factory, evt):
      policy = asyncio.get_event_loop_policy()
      policy.set_event_loop(policy.new_event_loop())
      server = factory()
      try:
         server.start()
      except ConnectionRefusedError as exc:
         evt.set()
      except ConnectionRefusedError as exc:
         evt.set()

   evt = multiprocessing.Event() # failure flag

   # start the server in another process and watch it fail
   sp = multiprocessing.Process(target=fail, args=(serviceklass, evt))
   sp.start()
   sp.join()

   assert evt.is_set()


@mark.parametrize('serviceklass', test_reconnecting)
def test_03_reconnect(serviceklass, with_delayed_mock_server):

   def connect(factory, evt):
      policy = asyncio.get_event_loop_policy()
      policy.set_event_loop(policy.new_event_loop())
      server = factory()
      signal.signal(signal.SIGTERM, server.stop)

      try:
         server.start()
      except WAMPSessionTimeoutError:
         pass
      except Exception as exc:
         evt.set()

   evt = multiprocessing.Event() # failure flag
   sp = multiprocessing.Process(target=connect, args=(serviceklass, evt))
   sp.start()
   time.sleep(8)
   sp.terminate()
   sp.join()
   assert not evt.is_set()

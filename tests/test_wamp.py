import asyncio
import multiprocessing
import signal
import time

from pytest import mark

from .servers import ConnectingWAMPService, ReConnectingWAMPService
from .fixtures import with_crossbar


tested = (ConnectingWAMPService, ReConnectingWAMPService)


@mark.parametrize('serviceklass', tested)
def test_01_join_realm(serviceklass, with_crossbar):

   def run_server(server):
      loop = asyncio.new_event_loop()
      asyncio.set_event_loop(loop)
      server.set_loop(loop)
      server.start()

   server = serviceklass()
   signal.signal(signal.SIGTERM, server.stop)
   p = multiprocessing.Process(target=run_server, args=(server,))
   p.start()
   time.sleep(2)
   p.terminate()
   p.join()


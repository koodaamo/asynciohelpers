from abc import abstractmethod, abstractproperty, ABCMeta

import logging
import os
import shutil
import time
import subprocess
import asyncio
import logging
import socketserver
import aiohttp
import aiohttp.server


from contextlib import contextmanager
from asynciohelpers.util import loggerprovider
from .util import logmethod, loggerprovider, logged


LOGLEVEL = logging.DEBUG


class DummyServiceImpl():
   "provide the implementables"

   async def _setup(self):
      self._logger.debug("%s setting up" % self.__class__.__name__)

   async def _run(self):
      self._logger.debug("%s runner running" % self.__class__.__name__)
      while True:
         await asyncio.sleep(2)

   async def _wait(self):
      self._logger.debug("%s waiter started" % self.__class__.__name__)
      while True:
         await asyncio.sleep(2)

   async def _teardown(self):
      self._logger.debug("%s tearing down" % self.__class__.__name__)


@logmethod("connection_lost")
@loggerprovider
class MockTransportServerProtocol(asyncio.Protocol):
   ""

   LOGLEVEL = LOGLEVEL

   @logged
   def connection_made(self, transport):
      self._transport = transport
      self._counter = 3

   def data_received(self, data):
      self._logger.debug("receiveing data from client: %s" % str(data))
      self._counter -= 1
      if self._counter == 0:
         self._logger.debug("will not receive any more, closing")
         self._transport.close()
      else:
         self._logger.debug("receiving %i more times" % self._counter)


def get_socket_server(loop, host, port):
   def factory():
      return MockTransportServerProtocol()
   return loop.create_server(factory, host, port)


def get_http_server(loop, host, port):
   def factory():
      return MockTransportServerProtocol()
   return loop.create_server(factory, host, port)


@logmethod("connection_lost")
@loggerprovider
class MockTransportServerProtocol(asyncio.Protocol):
   ""

   LOGLEVEL = LOGLEVEL

   @logged
   def connection_made(self, transport):
      self._transport = transport
      self._counter = 3

   def data_received(self, data):
      self._logger.debug("receiveing data from client: %s" % str(data))
      self._counter -= 1
      if self._counter == 0:
         self._logger.debug("will not receive any more, closing")
         self._transport.close()
      else:
         self._logger.debug("receiving %i more times" % self._counter)


@loggerprovider
class CloseNotifyingProtocol:

   LOGLEVEL = LOGLEVEL

   @logged
   def connection_lost(self, exc):
      self.is_closed.set_result(True)


@logmethod("connection_made")
@loggerprovider
class TransportServerProtocol(CloseNotifyingProtocol, asyncio.Protocol):

   LOGLEVEL = LOGLEVEL

   def connection_lost(self, exc):
      super().connection_lost(exc)



@loggerprovider
@logmethod("connection_made")
class TransportClientProtocol(CloseNotifyingProtocol, asyncio.Protocol):

   LOGLEVEL = LOGLEVEL

   def connection_lost(self, exc):
      super().connection_lost(exc)


@loggerprovider
class TCPHandler(socketserver.BaseRequestHandler):

   LOGLEVEL = LOGLEVEL

   def handle(self):
      self._logger.debug("mock handler called")
      # self.request is the TCP socket connected to the client
      data = self.request.recv(1024).strip()
      if data:
         self._logger.debug("test data received: %s" % data)


def get_socketserver(host, port, handler=TCPHandler):
   server = socketserver.TCPServer((host, port), handler, bind_and_activate=False)
   server.allow_reuse_address = True
   server.server_bind()
   server.server_activate()
   return server


class SingleHTTPRequestHandler(aiohttp.server.ServerHttpProtocol):

  async def handle_request(self, message, payload):
      response = aiohttp.Response(
          self.writer, 200, http_version=message.version
      )
      response.add_header('Content-Type', 'text/html')
      response.add_header('Content-Length', '18')
      response.send_headers()
      response.write(b'<h1>It Works!</h1>')
      await response.write_eof()

      # after serving a single request, shut down
      #self.shutdown()


def get_crossbar_binary():
   crossbar = shutil.which("crossbar") or os.environ.get("CROSSBAR")
   assert crossbar, "No crossbar found. Please point environment variable CROSSBAR to it."
   return crossbar


# context manager to start crossbar

@contextmanager
def crossbar_router():
   cb_exe = get_crossbar_binary()
   cdir = os.path.dirname(__file__)
   cdir = cdir[:cdir.rfind(os.path.sep)] + os.path.sep + "tests"
   print("using %s as crossbar config dir" % cdir)
   cbp = subprocess.Popen([cb_exe, "start", "--cbdir", cdir], stdout=subprocess.DEVNULL)
   time.sleep(4)
   yield cbp
   cbp.terminate()
   cbp.wait()
   return


class NotImplementedABC(metaclass=ABCMeta):

   @abstractproperty
   def _not_implemented_property(self):
      ""

   @abstractmethod
   def _not_implemented_method(self):
      ""

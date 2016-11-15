from abc import abstractmethod, abstractproperty, ABCMeta

import os, time, signal, logging
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

   def handle(self):
   # self.request is the TCP socket connected to the client
      while True:
         data = self.request.recv(1024).strip()
         if data:
            self._logger.debug("data received from socket: %s" % data)


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


# context manager to start crossbar

@contextmanager
def crossbar_router():
   CBCMD = os.environ.get("CROSSBAR")
   assert CBCMD, "Must have environment variable CROSSBAR set to crossbar binary path"
   cdir = os.path.dirname(__file__)
   cdir = cdir[:cdir.rfind(os.path.sep)] + os.path.sep + "tests"
   cbp = subprocess.Popen([CBCMD, "start", "--cbdir", cdir], stdout=subprocess.DEVNULL)
   time.sleep(4)
   yield cbp
   cbp.terminate()
   cbp.wait()
   return


# asynchronous version

@loggerprovider
class CrossbarRouter:

   def __init__(self, loop=None):
      self.loop = loop or asyncio.get_event_loop()

   async def __aenter__(self):
      CBCMD = os.environ.get("CROSSBAR")
      assert CBCMD, "Must have environment variable CROSSBAR set to crossbar binary path"
      cdir = os.path.dirname(__file__)
      cdir = cdir[:cdir.rfind(os.path.sep)] + os.path.sep + "tests"
      coro = asyncio.create_subprocess_exec(CBCMD, "start", "--cbdir", cdir, stdout=subprocess.DEVNULL, loop=self.loop)
      self.cbp = await coro
      await asyncio.sleep(3)
      self._logger.debug("started WAMP router with pid %i" % self.cbp.pid)

   async def __aexit__(self, exc_type, exc, tb):
      self.cbp.terminate()
      await self.cbp.wait()
      await asyncio.sleep(1, loop=self.loop)


class NotImplementedABC(metaclass=ABCMeta):

   @abstractproperty
   def _not_implemented_property(self):
      ""

   @abstractmethod
   def _not_implemented_method(self):
      ""

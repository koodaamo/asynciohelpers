import asyncio, logging

from asynciohelpers.util import loggerprovider, logged, logmethod
from .config import logger


class CloseNotifyingProtocol:

   @logged
   def connection_lost(self, exc):
      self.is_closed.set_result(True)


@logmethod("connection_lost")
@loggerprovider
class MockTransportServerProtocol(asyncio.Protocol):
   ""

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
@logmethod("connection_made")
class TransportClientProtocol(CloseNotifyingProtocol, asyncio.Protocol):

   def connection_lost(self, exc):
      super().connection_lost(exc)


@logmethod("connection_made")
@loggerprovider
class TransportServerProtocol(CloseNotifyingProtocol, asyncio.Protocol):

   def connection_lost(self, exc):
      super().connection_lost(exc)




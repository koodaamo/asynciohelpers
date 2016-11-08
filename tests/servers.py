"""
Server implementations that will be tested.
"""

import os, asyncio
from autobahn.asyncio.wamp import ApplicationSession

from asynciohelpers.util import loggerprovider, logged, logmethod
from asynciohelpers.service import AsyncioServiceBase
from asynciohelpers.service import AsyncioConnectingServiceBase
from asynciohelpers.service import AsyncioReConnectingServiceBase
from asynciohelpers.wamp import WAMPServiceMixin

from .protocols import TransportClientProtocol
from .protocols import TransportServerProtocol
from .config import TEST_HTTP_HOST, TEST_WAMP_HOST, TEST_WAMP_PORT, TEST_HTTP_PORT
from .components import WAMPComponent


class ConnectingAsyncioServer(AsyncioConnectingServiceBase):

   _host = TEST_HTTP_HOST
   _port = TEST_HTTP_PORT
   _transport_factory = TransportClientProtocol



@loggerprovider
class ReConnectingAsyncioServer(AsyncioReConnectingServiceBase):

   _host = TEST_HTTP_HOST
   _port = TEST_HTTP_PORT
   _transport_factory = TransportClientProtocol

   async def _run(self):
      self._logger.debug("running")
      while True:
         self._logger.debug("saying hello")
         self._transport.write(b"Hello world!")
         await asyncio.sleep(2, loop=self._loop)


@loggerprovider
class ConnectingWAMPService(WAMPServiceMixin, AsyncioConnectingServiceBase):

   wmp_url = "ws://%s:%i/ws" % (TEST_WAMP_HOST, TEST_WAMP_PORT)
   wmp_realm = "realm1"
   wmp_sessioncomponent = WAMPComponent


@loggerprovider
class ReConnectingWAMPService(WAMPServiceMixin, AsyncioReConnectingServiceBase):

   wmp_url = "ws://%s:%i/ws" % (TEST_WAMP_HOST, TEST_WAMP_PORT)
   wmp_realm = "realm1"
   wmp_sessioncomponent = WAMPComponent

"""
Server implementations that will be tested.
"""

import asyncio
from asynciohelpers.util import loggerprovider, wamp_configured
from asynciohelpers.service import AsyncioConnectingServiceBase
from asynciohelpers.service import AsyncioReConnectingServiceBase
from asynciohelpers.wamp import WAMPServiceMixin
from asynciohelpers.testing import TransportClientProtocol
from .config import TEST_HTTP_HOST, TEST_WAMP_HOST, TEST_WAMP_PORT, TEST_HTTP_PORT, LOGLEVEL
from .components import WAMPComponent


@loggerprovider
class ConnectingAsyncioServer(AsyncioConnectingServiceBase):

   _host = TEST_HTTP_HOST
   _port = TEST_HTTP_PORT
   _transport_factory = TransportClientProtocol

   LOGLEVEL = LOGLEVEL


@loggerprovider
class ReConnectingAsyncioServer(AsyncioReConnectingServiceBase):

   _host = TEST_HTTP_HOST
   _port = TEST_HTTP_PORT
   _transport_factory = TransportClientProtocol

   LOGLEVEL = LOGLEVEL

   async def _run(self):
      self._logger.debug("running")
      while True:
         self._logger.debug("saying hello")
         self._transport.write(b"Hello world!")
         await asyncio.sleep(2, loop=self._loop)


@loggerprovider
@wamp_configured
class ConnectingWAMPService(WAMPServiceMixin, AsyncioConnectingServiceBase):

   wmp_url = "ws://%s:%i/ws" % (TEST_WAMP_HOST, TEST_WAMP_PORT)
   wmp_realm = "realm1"
   wmp_sessioncomponent = WAMPComponent
   wmp_extra = None
   wmp_serializers = None

   LOGLEVEL = LOGLEVEL


@loggerprovider
@wamp_configured
class ReConnectingWAMPService(WAMPServiceMixin, AsyncioReConnectingServiceBase):

   wmp_url = "ws://%s:%i/ws" % (TEST_WAMP_HOST, TEST_WAMP_PORT)
   wmp_realm = "realm1"
   wmp_sessioncomponent = WAMPComponent
   wmp_extra = None
   wmp_serializers = None

   LOGLEVEL = LOGLEVEL

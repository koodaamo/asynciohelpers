"""
Server implementations that will be tested.
"""

import asyncio, threading
from asynciohelpers.util import loggerprovider, wamp_configured
from asynciohelpers.service import AsyncioConnecting
from asynciohelpers.service import AsyncioReConnecting
from asynciohelpers.wamp import WAMPServiceMixin
from asynciohelpers.testing import DummyServiceImpl, TransportClientProtocol
from .config import TEST_HTTP_HOST, TEST_WAMP_HOST, TEST_WAMP_PORT, TEST_HTTP_PORT, LOGLEVEL
from .components import WAMPComponent


@loggerprovider
class ConnectingAsyncioServer(AsyncioConnecting, DummyServiceImpl):

   _host = TEST_HTTP_HOST
   _port = TEST_HTTP_PORT
   _transport_factory = TransportClientProtocol

   LOGLEVEL = LOGLEVEL


@loggerprovider
class ReConnectingAsyncioServer(AsyncioReConnecting, DummyServiceImpl):

   _host = TEST_HTTP_HOST
   _port = TEST_HTTP_PORT
   _transport_factory = TransportClientProtocol

   LOGLEVEL = LOGLEVEL

   async def _run(self):
      self._logger.debug("runner running")

      while not self._closing:
         self._logger.debug("saying hello")
         try:
            self._transport.write(b"Hello world!")
         except Exception as exc:
            self._logger.warn("could not send: %s" % exc)
         await asyncio.sleep(2, loop=self._loop)

      self._logger.warn("runner stopped")


@loggerprovider
@wamp_configured
class ConnectingWAMPService(WAMPServiceMixin, AsyncioConnecting, DummyServiceImpl):

   def __init__(self, *args, **kwargs):
      super().__init__(*args, **kwargs)
      self._stop_event = threading.Event()

   wmp_url = u"ws://%s:%i/ws" % (TEST_WAMP_HOST, TEST_WAMP_PORT)
   wmp_realm = u"realm1"
   wmp_sessioncomponent = WAMPComponent
   wmp_extra = None
   wmp_serializers = None

   LOGLEVEL = LOGLEVEL


@loggerprovider
@wamp_configured
class ReConnectingWAMPService(WAMPServiceMixin, AsyncioReConnecting, DummyServiceImpl):

   wmp_url = u"ws://%s:%i/ws" % (TEST_WAMP_HOST, TEST_WAMP_PORT)
   wmp_realm = u"realm1"
   wmp_sessioncomponent = WAMPComponent
   wmp_extra = None
   wmp_serializers = None

   LOGLEVEL = LOGLEVEL

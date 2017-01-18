import asyncio
from autobahn.wamp.types import ComponentConfig
from autobahn.asyncio.websocket import WampWebSocketClientFactory


class WAMPSessionTimeoutError(asyncio.TimeoutError):
   ""

class WAMPServiceMixin:
   "base mixin that provides WAMP configuration plus transport and component factory"

   WAMP_SESSION_TIMEOUT = 3

   async def _connect(self):
      await super()._connect()
      try:
         await asyncio.wait_for(self._transport_factory._session_joined, self.WAMP_SESSION_TIMEOUT, loop=self._loop)
      except asyncio.TimeoutError as exc:
         err = "timeout (%is) establishing session" % self.WAMP_SESSION_TIMEOUT
         self._logger.warn(err)
         raise WAMPSessionTimeoutError(err)
      else:
         self._logger.debug("session established")

   @property
   def _transport_factory(self):
      "(optionally create and) return the transport factory"
      try:
         return self._created_transport_factory
      except:
         pass
      try:
         factory = WampWebSocketClientFactory(self._component, url=self.wmp_url, serializers=self.wmp_serializers, loop=self._loop)
      except Exception as exc:
         raise Exception("could not build transport factory: %s" % exc)
      else:
         factory._session_joined = asyncio.Future(loop=self._loop)
         self._logger.info("connecting to %s, realm '%s'" % (self.wmp_url, self.wmp_realm))
         self._created_transport_factory = factory
         return factory

   def _component(self):
      "component factory method that creates and returns the component"

      try:
         cfg = ComponentConfig(self.wmp_realm, self.wmp_extra)
      except Exception as exc:
         raise Exception("could not instantiate WAMP component config: %s" % str(exc))

      try:
         session = self.wmp_sessioncomponent(cfg)
      except Exception as exc:
         raise Exception("could not instantiate WAMP component: %s" % str(exc))
      else:
         session._loop = self._loop
         return session


   async def _wait(self):
      "default waiter"
      while True:
         await asyncio.sleep(900, self._loop)
         self._logger.info("waiting, still alive...")

   async def _run(self):
      "default runner"
      while True:
         await asyncio.sleep(900, self._loop)
         self._logger.info("running, still alive...")

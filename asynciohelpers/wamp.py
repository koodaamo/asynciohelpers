import asyncio
from autobahn.wamp.types import ComponentConfig
from autobahn.asyncio.websocket import WampWebSocketClientFactory
from autobahn.websocket.util import parse_url

from .util import loggerprovider


@loggerprovider
class WAMPServiceMixin:
   "base mixin that provides WAMP configuration plus transport and component factory"

   async def _connect(self):
      "wait all the way until component has joined"
      await super()._connect()
      self._protocol._session_joined = asyncio.Future(loop=self._loop)

   async def _setup(self):
      await super()._setup()
      await self._protocol._session_joined

   @property
   def _transport_factory(self):
      "create and return the transport factory"

      try:
         factory = WampWebSocketClientFactory(self._component, url=self.wmp_url, serializers=self.wmp_serializers, loop=self._loop)
      except Exception as exc:
         raise Exception("could not build transport factory: %s" % exc)
      else:
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


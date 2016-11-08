from autobahn.wamp.types import ComponentConfig
from autobahn.asyncio.websocket import WampWebSocketClientFactory
from autobahn.websocket.util import parse_url


class WAMPServiceMixin:
   "base mixin that provides WAMP configuration plus transport and component factory"

   wmp_url = None
   wmp_realm = None
   wmp_sessioncomponent = lambda x: None
   wmp_serializers = None
   wmp_ssl = None #  set to True or False for forced enable/disable
   wmp_extra = None # {"winservice": False} # by default not running as a Windows service


   @property
   def _transport_factory(self):
      "create and return the transport factory"

      assert hasattr(self, "wmp_url")
      assert hasattr(self, "wmp_serializers")

      try:
         factory = WampWebSocketClientFactory(self._component, url=self.wmp_url, serializers=self.wmp_serializers, loop=self._loop)
      except Exception as exc:
         raise Exception("could not build transport factory: %s" % exc)
      else:
         return factory


   def _component(self):
      "create and return the component factory"

      assert getattr(self, "wmp_realm", None) is not None

      try:
         cfg = ComponentConfig(self.wmp_realm, self.wmp_extra)
      except Exception as exc:
         raise Exception("could not instantiate WAMP component config: %s" % str(exc))

      try:
         session = self.wmp_sessioncomponent(cfg)
      except Exception as exc:
         raise Exception("could not instantiate WAMP component: %s" % str(exc))
      else:
         return session


   def __new__(cls, *args, **kwargs):

      (isSecureURL, host, port, resource, path, params) = parse_url(cls.wmp_url)

      cls._host = host
      cls._port = port

      if not getattr(cls, "wmp_ssl", None):
         cls._ssl = isSecureURL
      elif cls.wmp_ssl and not isSecureURL:
         raise RuntimeError(
            'the wmp_ssl class variable of %s conflicts with the "ws:" prefix '
            'of the wmp_url variable. Did you mean to use "wss:"?' % cls.__name__)
      else:
         cls._ssl = cls.wmp_ssl

      return object.__new__(cls)

from abc import abstractproperty
import os, logging, signal, types
from autobahn.websocket.util import parse_url


def env_configured(cls):
   "get _host, _port, and _ssl from CONNECT_HOST, CONNECT_PORT & CONNECT_SSL env vars"

   host = os.environ.get("CONNECT_HOST")
   if host:
      cls._host = host
   port = os.environ.get("CONNECT_PORT")
   if port:
      cls._port = port
   ssl = os.environ.get("CONNECT_SSL")
   if ssl:
      cls._ssl = ssl
   return cls


def wamp_configured(cls):
   "get host, port & ssl from wmp_url"

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

   return cls


def wamp_env_configured(cls):
   "get wmp_url & wmp_realm from WAMP_ROUTER_URL & WAMP_REALM env vars"

   envvar = os.environ.get("WAMP_ROUTER_URL")
   if envvar:
      cls.wmp_url = envvar

   envvar = os.environ.get("WAMP_ROUTER_REALM")
   if envvar:
      cls.wmp_realm = envvar

   return cls


def signalled(signalvalue):
   "decorate a method to be called upon signal"

   def deco(f):
      signal.signal(signalvalue, f)
      return f

   return deco


def loggerprovider(cls):
   "bind the global logger to class, or create new using class name"
   cls._logger = logging.getLogger(cls.__name__)
   level = getattr(cls, "LOGLEVEL", None) or logging.INFO
   cls._logger.setLevel(level)
   return cls


def logged(*args):
   "decorate a method to log, optionally with a level"

   def wrapped(method, lvl):

      def wrapper(self, *args, **kwargs):
         self._logger.log(lvl, "%s called" % method.__name__)
         return method(self, *args, **kwargs)

      return wrapper

   if type(args[0]) == types.FunctionType:
      # no level given, args[0] is the decorated method
      return wrapped(args[0], logging.DEBUG)

   else:
      # args[0] has level
      def deco(method):
         return wrapped(method, args[0])

      return deco


def logmethod(name, *args, **kwargs):
   "just add a logging method call, optionally with a level"

   lvl = args[0] if args else logging.DEBUG
   async = True if kwargs.get("async") else False

   def deco(cls):
      "actual decorator"

      def wrapper(self, *args, **kwargs):
         self._logger.log(lvl, "%s called" % name)
         if async:
            yield

      loggermethod =  types.MethodType(wrapper, cls)
      setattr(cls, name, loggermethod)

      return cls

   return deco


def isabstractmethod(obj):
   is_function = isinstance(obj, types.FunctionType)
   has_name = obj.__class__.__name__ == "abstractmethod"
   return is_function and has_name


def provides_abc(klass, abc):
   "whether or not a class provides an abc"
   members = list(abc.__dict__.items())
   attrs = [k for k,v in members if isinstance(v, abstractproperty)]
   methods = [k for k,v in members if isabstractmethod(v)]
   for member in attrs + methods:
      if not any(member in base.__dict__ for base in klass.__mro__):
         return False
   return True



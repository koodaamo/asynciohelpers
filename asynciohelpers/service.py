from functools import partial
from contextlib import suppress
import asyncio
from concurrent.futures import CancelledError
import txaio
from .abcs import ServiceBaseABC
from .exceptions import SetupException
from .util import loggerprovider



class AsyncioServiceBase:
   "base SIGTERM-stoppable base class that just sets up and runs the loop"

   # these three required per the ABC
   _host = None
   _port = None
   _ssl = None

   _loop = None
   _external_loop = False

   def __init__(self, loop=None):
      if loop:
         self._loop = loop
         self._external_loop = True

   async def _setup(self):
      self._logger.debug("%s setting up" % self.__class__.__name__)

   async def _run(self):
      self._logger.debug("%s running" % self.__class__.__name__)

   async def _teardown(self):
      self._logger.debug("%s tearing down" % self.__class__.__name__)

      with suppress(asyncio.CancelledError):
         self._runner.cancel()


   def start(self):

      self._loop = self._loop or asyncio.get_event_loop()
      txaio.use_asyncio()
      txaio.config.loop = self._loop
      #txaio.start_logging(level='info')

      self._logger.info("%s start requested" % self.__class__.__name__)
      self._closing = False
      self._started = asyncio.Future(loop=self._loop)

      # start the runner coro after setup is done, or exit if error

      def setup_finished(future):
         exc = future.exception()
         if exc:
            self._logger.warn("setup failed, stopping immediately: %s" % str(exc))
            setup_failed = SetupException("failure: %s" % str(exc))
            self._started.set_exception(setup_failed)
         else:
            self._runner = self._loop.create_task(self._run())
            self._started.set_result(True)

      self._setup_task = self._loop.create_task(self._setup())

      if self._external_loop:
         self._setup_task.add_done_callback(setup_finished)
         return self._started
      else:
         try:
            self._loop.run_until_complete(self._setup_task)
         except Exception as exc:
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._logger.warn("setup failed, stopping immediately: %s" % str(exc))
            raise SetupException("failure: %s" % str(exc)) from None
         self._loop.run_forever()
         self._closing = True


   def stop(self, *args, **kwargs):
      self._logger.info("%s stop requested" % self.__class__.__name__)
      self._stopped = asyncio.Future(loop=self._loop)
      self._closing = True

      def on_teardown_complete(future):
         self._stopped.set_result(True)

      self._loop.create_task(self._teardown()).add_done_callback(on_teardown_complete)

      if self._external_loop:
         return self._stopped
      else:
         self._loop.call_soon_threadsafe(self._loop.stop)



class AsyncioConnectingServiceBase(AsyncioServiceBase):
   "asyncio service that connects a given transport"

   _transport_factory = None # protocol class, or other instance factory
   _host = None # FQDN
   _port = None # int
   _ssl = False # bool

   async def _connect(self):
      args = (self._transport_factory,)
      kwargs = {"host": self._host, "port": self._port, "ssl": self._ssl}
      connector = self._loop.create_connection(*args, **kwargs)
      (self._transport, self._protocol) = await connector
      self._logger.debug("connected transport %s" % self._transport)
      self._protocol.is_closed = asyncio.Future(loop=self._loop)

   async def _setup(self):
      self._logger.debug("setting up")
      await self._connect()

   async def _teardown(self):
      self._logger.debug("teardown")

      try:
         self._transport.close()
      except Exception as exc:
         self._logger.warn("cannot close transport: %s" % exc)

      await self._protocol.is_closed
      await super()._teardown()



class AsyncioReConnectingServiceBase(AsyncioConnectingServiceBase):
   "asyncio service that connects a given transport"

   async def _connect(self):
      "after super() setup has run, register a protocol close (re)connect callback"

      while not self._closing:
         self._logger.debug("attempting connect")
         try:
            result = await super()._connect()
         except ConnectionError as exc:
            self._logger.error("connection refused, retrying: %s" % str(exc))
         except CancelledError as exc:
            self._logger.error("connect cancelled, stopping: %s" % str(exc))
            break
         except SetupException as exc:
            self._logger.error("setup failed: %s" % exc)
            break
         except Exception as exc:
            self._logger.error("unhandled error %s: %s" % (type(exc), exc))
         else:
            self._protocol.is_closed.add_done_callback(self._reconnect)
            self._logger.debug("transport connected")
            break
         await asyncio.sleep(2, loop=self._loop)

   def _reconnect(self, future):
      if not self._closing:
         self._logger.error("connection lost, reconnecting")
         reconnect = self._loop.create_task(self._connect())

         def reconnected(future):
            runner = self._loop.create_task(self._run())

         reconnect.add_done_callback(reconnected)



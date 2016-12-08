from contextlib import suppress
import asyncio
from concurrent.futures import CancelledError
from .exceptions import SetupException


class AsyncioRunning:
   "base runner class that sets up and runs the loop & payload"

   RESTART_DELAY = 15 # seconds until waiter & runner are restarted

   # these three required per the ABC
   _host = None
   _port = None
   _ssl = None

   _loop = None
   _external_loop = False

   def set_loop(self, loop):
      self._loop = loop
      self._external_loop = True


      with suppress(asyncio.CancelledError):
         self._run_task.cancel()
         self._wait_task.cancel()

      self._transport.close()
      await asyncio.sleep(0)


   def start(self):

      self._loop = self._loop or asyncio.get_event_loop()
      self._logger.debug("%s start requested" % self.__class__.__name__)

      self._closing = False
      self._started = asyncio.Future(loop=self._loop)

      # start the runner coro after setup is done, or exit if error

      def setup_finished(future):
         exc = future.exception()
         if exc:
            self._logger.error("setup failed, stopping immediately: %s" % str(exc))
            setup_failed = SetupException("failure: %s" % str(exc))
            self._started.set_exception(setup_failed)
         else:
            self._logger.debug("setup completed ok")
            self._wait_task = self._loop.create_task(self._wait())
            self._run_task = self._loop.create_task(self._run())
            self._started.set_result(True)

      self._setup_task = self._loop.create_task(self._setup())

      if self._external_loop:
         self._setup_task.add_done_callback(setup_finished)
         self._wait_task = self._loop.create_task(self._wait())
         self._run_task = self._loop.create_task(self._run())
         return self._started
      else:
         try:
            self._loop.run_until_complete(self._setup_task)
         except Exception as exc:
            self._logger.warn("setup failed, stopping: %s" % str(exc))
            self._loop.call_soon_threadsafe(self._loop.stop)
            raise SetupException("failure: %s" % str(exc)) from None

         def wait_completed(task):
            self._run_task.cancel()

         # we can be stopped either via SvcStop -> waiter fallback, or
         # direct call to stop(), so _closing synchronizes action
         while not self._closing:

            # when the waiter completes, the runner gets cancelled
            self._wait_task = self._loop.create_task(self._wait())
            self._run_task = self._loop.create_task(self._run())
            self._wait_task.add_done_callback(wait_completed)

            try:
               self._loop.run_until_complete(asyncio.gather(self._wait_task, self._run_task))
            except CancelledError:
               self._logger.debug("waiter/runner cancelled")
            except Exception as exc:
               self._logger.error("wait/run task failure: %s" % str(exc))
            restart_waiter = asyncio.sleep(self.RESTART_DELAY, loop=self._loop)
            self._loop.run_until_complete(restart_waiter)

         self.stop()
         self._loop.close()
         self._logger.warn("%s is now shut down" % self.__class__.__name__)


   def stop(self, *args, **kwargs):
      self._closing = True
      self._teardown_task = self._loop.create_task(self._teardown())

      if self._external_loop:
         return self._teardown_task
      else:
         try:
            self._loop.run_until_complete(self._teardown_task)
         except Exception as exc:
            self._logger.warn(exc)
         try:
            self._loop.call_soon_threadsafe(self._loop.stop)
         except Exception as exc:
            self._logger.warn(exc)



class AsyncioConnecting(AsyncioRunning):
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
      self._protocol.is_closed = asyncio.Future(loop=self._loop)
      self._logger.debug("connected transport (%s)" % self._transport.__class__.__name__)

   async def _setup(self):
      self._logger.debug("connecting")
      await self._connect()

   async def _teardown(self):
      self._logger.debug("teardown starting")

      # wait for base class to cancel tasks
      await super()._teardown()

      # wait for the transport to close
      self._logger.debug("closing transport")
      try:
         self._transport.close()
      except Exception as exc:
         self._logger.warn("cannot close transport: %s" % exc)

      # protocol implementation MUST set this:
      await self._protocol.is_closed


class AsyncioReConnecting(AsyncioConnecting):
   "asyncio service that connects a given transport"

   RECONNECT_DELAY = 5 # seconds

   async def _connect(self):
      "after super() setup has run, register a protocol close (re)connect callback"

      await asyncio.sleep(self.RECONNECT_DELAY, loop=self._loop)

      while not self._closing:
         self._logger.debug("attempting connect")
         try:
            result = await super()._connect()
         except ConnectionError as exc:
            self._logger.warn("connection refused, retrying: %s" % str(exc))
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
            break
         await asyncio.sleep(self.RECONNECT_DELAY, loop=self._loop)

   def _reconnect(self, future):
      if not self._closing:
         self._logger.warn("connection lost, reconnecting")
         reconnect = self._loop.create_task(self._connect())
      else:
         self._logger.warn("already closing, not reconnecting")


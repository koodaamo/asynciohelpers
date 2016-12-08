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


   def _on_wait_completed(self, *args):
      "also stop the runner when waiting is complete"
      self._closing = True
      try:
         self._run_task.cancel()
      except:
         # it's possible the runnables have not been created yet...
         pass


   def start(self):

      self._loop = self._loop or asyncio.get_event_loop()
      self._logger.debug("%s start requested" % self.__class__.__name__)

      self._closing = False
      self._started = asyncio.Future(loop=self._loop)

      # start the runner coro after setup is done, or exit if error

      self._wait_task = self._loop.create_task(self._wait())
      self._wait_task.add_done_callback(self._on_wait_completed)

      def setup_complete(future):
         exc = future.exception()
         if exc:
            self._logger.error("setup failed, stopping immediately: %s" % str(exc))
            setup_failed = SetupException("failure: %s" % str(exc))
            self._started.set_exception(setup_failed)
         else:
            self._logger.debug("setup completed ok, scheduling runner")
            self._run_task = self._loop.create_task(self._run())
            self._started.set_result(True)

      self._setup_task = self._loop.create_task(self._setup())
      self._setup_task.add_done_callback(setup_complete)

      if self._external_loop:
         return self._started

      # run the setup
      try:
         self._loop.run_until_complete(self._setup_task)
      except Exception as exc:
         self._wait_task.cancel()
         self._loop.call_soon_threadsafe(self._loop.stop)

      # run the main loop; we can be stopped either by waiter completing & canceling
      # runner or by stop(), which actually just cancels the waiter

      while not self._closing:

         try:
            self._loop.run_until_complete(self._run_task)
         except CancelledError:
            self._logger.info("runner cancelled")
            break
         except KeyboardInterrupt:
            self._logger.info("runner terminated by user action")
            self._wait_task.cancel()
            break
         except Exception as exc:
            self._logger.error("runner failure: %s" % str(exc))
            self._delaying = asyncio.sleep(self.RESTART_DELAY, loop=self._loop)
            self._loop.run_until_complete(self._delaying)
            if not self._closing:
               self._run_task = self._loop.create_task(self._run())

      self._teardown_task = self._loop.create_task(self._teardown())

      try:
         self._loop.run_until_complete(self._teardown_task)
      except Exception as exc:
         self._logger.warn("teardown problem: %s" % exc)

      remaining = asyncio.Task.all_tasks()
      for task in remaining:
         task.cancel()

      try:
         self._loop.run_until_complete(asyncio.gather(*remaining))
      except CancelledError:
         pass
      except Exception as exc:
         self._logger.warn("cleanup failure: %s" % exc)
      try:
         self._loop.call_soon_threadsafe(self._loop.stop)
      except Exception as exc:
         self._logger.warn(str(exc))

      self._loop.close()
      self._logger.info("%s is now shut down" % self.__class__.__name__)


   def stop(self, *args, **kwargs):
      "cancel the task and return the stop future if external loop"

      self._logger.info("stop requested")
      self._wait_task.cancel()

      if self._external_loop:
         self._teardown_task = self._loop.create_task(self._teardown())
         return self._teardown_task



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


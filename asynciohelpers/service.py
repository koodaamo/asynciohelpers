import signal
import asyncio
import txaio
from concurrent.futures import CancelledError


class AsyncioRunning:
   "base runner class that sets up and runs the loop & payload"

   RUNNER_RESTART_ON_FAIL = True
   RUNNER_RESTART_ON_COMPLETION = True

   FAILURE_RESTART_DELAY = 5 # seconds
   COMPLETION_RESTART_DELAY = 5 #

   # these three required per the ABC
   _host = None
   _port = None
   _ssl = None
   _loop = None
   _external_loop = False
   _closing = False

   def set_loop(self, loop=None):
      if loop:
         self._loop = loop
         self._external_loop = True
      elif not self._loop:
         self._loop = asyncio.get_event_loop()
      else:
         pass # if loop exists and was not explicitly given, just fall through


   def _on_wait_completed(self, f):
      "stop the service runner when waiting is complete"
      try:
         # the order matters here
         self._closing = True
         self._start_task.cancel()
      except:
         pass
      self._logger.debug("service (-start) task cancelled")


   async def _start(self):

      # need to explicitly enable txaio :(
      txaio.use_asyncio()
      txaio.config.loop = self._loop

      # set up signal handler if possible
      try:
         self._loop.add_signal_handler(signal.SIGTERM, self.stop)
      except:
         pass # ignore if we're on Windows

      # setup background waiter task - note that if the waiter completes early,
      # it will cancel this present task (_start)
      self._wait_task = self._loop.create_task(self._wait())
      self._wait_task.add_done_callback(self._on_wait_completed)

      # call the subclass API to eg. connect to router
      await self._setup()

      while not self._closing:

         try:
            # call the subclass API for running any payload
            await self._run()
         except CancelledError:
            self._logger.debug("runner cancelled")
            break
         except Exception as exc:
            self._logger.error("runner failed: %s" % str(exc))
            if self.RUNNER_RESTART_ON_FAIL:
               self._logger.debug("runner restart in %i seconds" % self.FAILURE_RESTART_DELAY)
               await asyncio.sleep(self.RESTART_DELAY, loop=self._loop)
            else:
               self._closing = True
         else:
            self._logger.debug("runner completed")
            if self.RUNNER_RESTART_ON_COMPLETION:
               pass
            else:
               self._closing = True


   def start(self):
      "main public API method for starting the server"

      self._logger.info("%s start requested" % self.__class__.__name__)

      self.set_loop()

      # SERVICE START
      self._start_task = self._loop.create_task(self._start())
      try:
         self._loop.run_until_complete(self._start_task)
      except CancelledError:
         self._logger.debug("service cancelled")
      except KeyboardInterrupt:
         self._logger.debug("service terminated by user action")

      # TEARDOWN
      self._logger.debug("service teardown starting")
      self._teardown_task = self._loop.create_task(self._teardown())
      self._loop.run_until_complete(self._teardown_task)

      # CLEANUP
      incomplete = [t for t in asyncio.Task.all_tasks() if not t.done()]
      cleaning = asyncio.gather(*incomplete)
      cleaning.cancel()
      try:
         self._loop.run_until_complete(cleaning)
      except CancelledError:
         pass # this should happen, it's ok
      except Exception as exc:
         self._logger.warn("task raised %s exception at cleanup: %s" % (type(exc), exc))

      # STOP & CLOSE LOOP
      self._loop.call_soon_threadsafe(self._loop.stop)
      self._loop.close()
      self._logger.info("%s is now shut down" % self.__class__.__name__)


   def stop(self, *args, **kwargs):
      "main public API method for stopping the server"
      self._logger.info("stop requested")
      # stop the waiter, which will stop the start task
      self._wait_task.cancel()



class AsyncioConnecting(AsyncioRunning):
   "asyncio service that connects a given transport"

   _transport_factory = None # protocol class, or other instance factory
   _host = None # FQDN
   _port = None # int
   _ssl = False # bool
   _timeout = 2

   async def _connect(self):
      self._cargs = {"host": self._host, "port": self._port, "ssl": self._ssl}
      self._logger.debug("connecting to {host}:{port} (ssl: {ssl})".format(**self._cargs))
      self._logger.debug("using transport factory: %s" % self._transport_factory)
      connector = self._loop.create_connection(self._transport_factory, **self._cargs)
      connector_with_timeout = asyncio.wait_for(connector, self._timeout, loop=self._loop)
      (self._transport, self._protocol) = await connector_with_timeout
      self._protocol.is_closed = asyncio.Future(loop=self._loop)
      self._logger.debug("connected transport (%s)" % self._transport.__class__.__name__)
      self._logger.debug("using protocol %s" % self._protocol.__class__.__name__)

   async def _setup(self):
      await self._connect()
      self._logger.info("connected to {host}:{port} (ssl: {ssl})".format(**self._cargs))

   async def _teardown(self):
      self._logger.debug("closing transport")

      try:
         self._transport.close()
      except Exception as exc:
         pass # if we never connected, no point in making noise here

      try:
         # protocol implementation must set is_closed
         await self._protocol.is_closed
      except Exception as exc:
         pass # if we never connected, no point in making noise here



class AsyncioReConnecting(AsyncioConnecting):
   "asyncio service that connects a given transport"

   RECONNECT_DELAY = 1 # seconds
   RECONNECT_MAX_TIMES = 3

   async def _connect(self):
      "after super() setup has run, register a protocol close (re)connect callback"

      await asyncio.sleep(self.RECONNECT_DELAY, loop=self._loop)

      RETRIES = 0

      while not self._closing:
         try:
            result = await super()._connect()
         except Exception as exc:
            # if connection fails right here, we just wait a bit and retry
            self._logger.warn("connection attempt failed: %s" % exc)

            if self.RECONNECT_MAX_TIMES:
               if RETRIES < self.RECONNECT_MAX_TIMES:
                  retries_left = self.RECONNECT_MAX_TIMES - RETRIES - 1
                  msg = "reconnecting in %i seconds, %i retries left after that"
                  self._logger.info(msg % (self.RECONNECT_DELAY, retries_left))
                  RETRIES += 1
               else:
                  self._logger.warn("no connection retries left, giving up!")
                  raise
            else:
               self._logger.info("reconnecting in %i seconds" % self.RECONNECT_DELAY)

            await asyncio.sleep(self.RECONNECT_DELAY, loop=self._loop)

         else:
            # register a reconnect callback if connection fails later
            self._protocol.is_closed.add_done_callback(self._reconnect)
            return # important to return right here

      # we're closing, so remove the reconnect callback to avoid extra noise
      self._protocol.is_closed.remove_done_callback(self._reconnect)


   def _reconnect(self, future):
      if not self._closing:
         reconnect = self._loop.create_task(self._connect())
      else:
         self._logger.debug("already closing, not reconnecting")


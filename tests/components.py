""" WAMP components used for testing """

from autobahn.asyncio.wamp import ApplicationSession
from asynciohelpers.util import loggerprovider

from .config import LOGLEVEL


@loggerprovider
class WAMPComponent(ApplicationSession):

   LOGLEVEL = LOGLEVEL

   def onJoin(self, details):
      self._logger.debug("joined realm: '%s'" % details.realm)
      self._transport.factory._session_joined.set_result(True)

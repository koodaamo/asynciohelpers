""" WAMP components used for testing """

import asyncio
from autobahn.asyncio.wamp import ApplicationSession
from asynciohelpers.util import loggerprovider, logged, logmethod

from .config import LOGLEVEL


@loggerprovider
class WAMPComponent(ApplicationSession):

   LOGLEVEL = LOGLEVEL

   @logged
   def onJoin(self, details):
      self._transport.factory._session_joined.set_result(True)

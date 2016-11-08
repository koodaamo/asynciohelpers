""" WAMP components used for testing """

import logging
from autobahn.asyncio.wamp import ApplicationSession
from asynciohelpers.util import loggerprovider, logged, logmethod


@loggerprovider
@logmethod("onJoin", async=True)
class WAMPComponent(ApplicationSession):
   ""

   @logged
   async def onConnect(self):
      super().onConnect()

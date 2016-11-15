import sys, time, asyncio, logging, signal, multiprocessing, inspect
from pytest import raises, mark, fixture

from asynciohelpers.service import AsyncioServiceBase
from asynciohelpers.exceptions import SetupException

from .fixtures import with_mock_server
from .servers import ConnectingAsyncioServer, ReConnectingAsyncioServer
from .servers import ConnectingWAMPService, ReConnectingWAMPService
from .config import TEST_HOST, TEST_PORT, logger


tested_services = (ConnectingAsyncioServer,
                   ReConnectingAsyncioServer,
                   ConnectingWAMPService,
                   ReConnectingWAMPService
                   )


@fixture(scope="module", params=tested_services)
def servicefactory(request):
   "run tests for each server"
   yield request.param
   return


def test_01_instantiate_succeeds(servicefactory):
   "all servers can be instantiated"
   assert servicefactory in tested_services
   servicefactory()






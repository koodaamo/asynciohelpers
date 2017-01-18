import multiprocessing
import os
import subprocess
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from pytest import fixture

from .config import TEST_HTTP_HOST, TEST_HTTP_PORT, logger
from asynciohelpers.testing import get_crossbar_binary
from asynciohelpers.testing import get_socketserver


@fixture(scope="function")
def with_mock_server():
   "starts a basic TCP server at TEST_HTTP_HOST, TEST_HTTP_PORT"

   def run_mock_server():
      server = get_socketserver(TEST_HTTP_HOST, TEST_HTTP_PORT)
      try:
         server.serve_forever()
      except (KeyboardInterrupt, SystemExit):
         server.server_close()

   ms = multiprocessing.Process(target=run_mock_server)
   ms.start()
   yield
   ms.terminate()
   ms.join()


@fixture(scope="function")
def with_delayed_mock_server():
   "starts a basic TCP server after 2 seconds at TEST_HTTP_HOST, TEST_HTTP_PORT"

   def run_mock_server():
      # wait first, let a connection fail
      time.sleep(1.5)

      # bring it up, let any reconnect kick in
      logger.debug("mock server starting in 1.5")
      server = get_socketserver(TEST_HTTP_HOST, TEST_HTTP_PORT)
      server.handle_request()
      time.sleep(0.2)

      # cause connection failure by shutdown
      #logger.warn("mock server shutting down")
      #server.shutdown()
      logger.warn("mock server closing")
      server.server_close()
      time.sleep(2)

      # bring it up again, for good
      logger.debug("mock server rising again, to serve forever")
      server = get_socketserver(TEST_HTTP_HOST, TEST_HTTP_PORT)
      try:
         server.serve_forever()
      except (KeyboardInterrupt, SystemExit):
         server.server_close()

   ms = multiprocessing.Process(target=run_mock_server)
   ms.start()
   yield
   ms.terminate()
   ms.join()



@fixture
def with_mock_httpd():

   def run_mock_server(server_class=HTTPServer, handler_class=BaseHTTPRequestHandler):
      server_address = (TEST_HTTP_HOST, TEST_HTTP_PORT)
      httpd = server_class(server_address, handler_class)
      httpd.serve_forever()

   ms = multiprocessing.Process(target=run_mock_server)
   ms.start()
   time.sleep(0.1)
   yield
   ms.terminate()
   ms.join()


@fixture(scope="module")
def with_reconnecting_mock_httpd():

   def run_mock_server(server_class=HTTPServer, handler_class=BaseHTTPRequestHandler):
      server_address = (TEST_HTTP_HOST, TEST_HTTP_PORT)
      httpd = server_class(server_address, handler_class)
      httpd.serve_forever()

   ms = multiprocessing.Process(target=run_mock_server)
   ms.start()
   time.sleep(0.1)
   yield
   ms.terminate()
   ms.join()


@fixture(scope="module")
def with_crossbar():
   "start up crossbar"
   cb_exe = get_crossbar_binary()
   cdir = os.path.dirname(__file__)
   cbp = subprocess.Popen([cb_exe, "start", "--cbdir", cdir], stdout=subprocess.DEVNULL)
   logger.info("started crossbar, using %s as crossbar config dir" % cdir)
   time.sleep(2)
   yield cbp
   cbp.terminate()
   cbp.wait()
   return



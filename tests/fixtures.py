import time, multiprocessing, socketserver, subprocess
import aiohttp
import aiohttp.server
from http.server import HTTPServer, BaseHTTPRequestHandler
from pytest import fixture

from .config import TEST_HTTP_HOST, TEST_HTTP_PORT
from .utils import TCPHandler


@fixture(scope="function")
def with_mock_server():

   def run_mock_server():
      while True:
         try:
            server = socketserver.TCPServer((TEST_HTTP_HOST, TEST_HTTP_PORT), TCPHandler)
         except OSError as exc:
            time.sleep(0.2)
         else:
            server.serve_forever()

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


@fixture
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
def crossbar():
   "start up crossbar"
   p = subprocess.Popen(["crossbar", "start"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
   yield
   p.terminate()
   #p.wait()


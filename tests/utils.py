import asyncio
import logging
import socketserver
import aiohttp
import aiohttp.server

from asynciohelpers.util import loggerprovider

from .protocols import MockTransportServerProtocol


def get_socket_server(loop, host, port):
   def factory():
      return MockTransportServerProtocol()
   return loop.create_server(factory, host, port)


def get_http_server(loop, host, port):
   def factory():
      return MockTransportServerProtocol()
   return loop.create_server(factory, host, port)


@loggerprovider
class TCPHandler(socketserver.BaseRequestHandler):

   def handle(self):
   # self.request is the TCP socket connected to the client
      while True:
         data = self.request.recv(1024).strip()
         if data:
            self._logger.debug("data received from socket: %s" % data)


class SingleHTTPRequestHandler(aiohttp.server.ServerHttpProtocol):

  async def handle_request(self, message, payload):
      response = aiohttp.Response(
          self.writer, 200, http_version=message.version
      )
      response.add_header('Content-Type', 'text/html')
      response.add_header('Content-Length', '18')
      response.send_headers()
      response.write(b'<h1>It Works!</h1>')
      await response.write_eof()

      # after serving a single request, shut down
      #self.shutdown()

#!env python
# $Id: $
# ==============================================================================
# gevent modifications:
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
# ==============================================================================
# original code:
# Copyright 2008 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
#
# Asynchronous and threaded socket servers for the sendmail milter protocol.
#
# Example usage:
#"""
#   import asyncore
#   import ppymilterserver
#   import ppymilterbase
#
#   class MyHandler(ppymilterbase.PpyMilter):
#     def OnMailFrom(...):
#       ...
#   ...
#
#   # to run async server
#   server = PPYMilterServer(listener=(host, port),
#                            handler=MyHandler).server
#   server.serve_forever()
#"""
#

__author__ = 'Eric DeFriez'

from gevent import monkey 
monkey.patch_socket()
from gevent.server import StreamServer

import binascii
import logging
import ppymilterbase
import struct
import sys


MILTER_LEN_BYTES = 4  # from sendmail's include/libmilter/mfdef.h

class PPYMilterHandler(object):

    sockfile = None
    handler = None

    def _read(self):
        sread = self.sockfile.read(MILTER_LEN_BYTES)
        if sread == '':
            return None
        logging.info (' l<< "%s" (%d)' % (repr(sread), len(sread)))
        packetlen = int(struct.unpack('!I', sread)[0])
        inbuf = []
        read = 0
        while read < packetlen:
            partial = self.sockfile.read(packetlen - read)
            inbuf.append(partial)
            read += len(partial)
        out = ''.join(inbuf)
        logging.info(' <<< %s', binascii.b2a_qp(out))
        return out

    def _send(self, response):
        self.sockfile.write(struct.pack('!I', len(response)))
        self.sockfile.write(response)
        self.sockfile.flush()
        logging.info(' >>> %s', binascii.b2a_qp(response))

    def __init__(self, socket, address, **kw):
        logging.info('vvvv New connection from %s:%s' % address)
        if self.sockfile is not None:
            logging.info(" === closing existing socketfile")
            self.sockfile.close()
        self.sockfile = socket.makefile()
        self._dispatch = ppymilterbase.PpyMilterDispatcher(self.handler)
        try:
            while True:
                data = self._read()
                if data is None or data == '':
                    break;
                response = self._dispatch.Dispatch(data)
                if type(response) == list:
                    for r in response:
                        self._send(r)
                elif response:
                    self._send(response)
        except Exception, e:
            import pdb; pdb.set_trace();
            logging.error('Unhandled Exception %s' % repr(e))
        finally:
            if self.sockfile:
                self.sockfile.close()
            self.sockfile = None
            logging.info(' ^^^ closing session ^^^')


class PPYMilterServer(object):

    server = None

    def __init__(self, listener, handler=ppymilterbase.PpyMilter):
        milter_handler = PPYMilterHandler
        milter_handler.handler = handler
        self.server = StreamServer(listener, milter_handler)


# Allow running the library directly to demonstrate a simple example invocation.
if __name__ == '__main__':
  port = 9999
  try: 
      port = sys.argv[1]
  except Exception: 
      pass

  logging.basicConfig(level=logging.DEBUG,
                      format='%(asctime)s %(levelname)s %(message)s',
                      datefmt='%Y-%m-%d@%H:%M:%S')
  server = PPYMilterServer(listener=('0', port),
          handler=ppymilterbase.PpyMilter).server
  server.serve_forever()


#!/usr/bin/env python
import asyncio
import json

from pyDBMS.cursor import Cursor

__author__ = 'litleleprikon'


TYPE_CREATE_CURSOR = 'CREATE_CURSOR'
STATUS_SUCCESS = 'SUCCESS'
HOST = 'localhost'
PORT = 5657


class DBMSError(Exception):
    pass


async def connect(loop, host='localhost', port=5657):
    reader, writer = await asyncio.open_connection(host, port, loop=loop)
    return Connection(reader, writer)


class Connection:
    def __init__(self, reader, writer):
        self._reader = reader
        self._writer = writer

    def send_message(self, message):
        if message[-1] != '\n':
            message += '\n'
        self._writer.write(message.encode())

    async def get_response(self):
        lines = []
        while not self._reader.at_eof():
            lines.append((await self._reader.readline()).decode())
        return '\n'.join(lines)

    async def _send_cursor_request(self):
        self.send_message(json.dumps({'qtype': TYPE_CREATE_CURSOR}))
        response = await self.get_response()
        parsed_response = json.loads(response)
        if response['status'] == STATUS_SUCCESS:
            return response['cur_id']
        else:
            raise DBMSError(response['error'])

    async def cursor(self):
        _id = await self._send_cursor_request()
        return Cursor(_id, self)

    def close(self):
        pass

    def __del__(self):
        self._writer.close()


async def run(loop):
    pass


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.ensure_future(run(loop)))
    loop.close()

if __name__ == '__main__':
    main()

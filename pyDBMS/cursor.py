#!/usr/bin/env python
import json

from pyDBMS.convert import escape_item, convert_data

__author__ = 'litleleprikon'

TYPE_QUERY = 'QUERY'
TYPE_FETCH = 'FETCH'
DEFAULT_FETCH_NUM = 10


class Cursor:
    def __init__(self, _id, connection):
        self._id = _id
        self._connection = connection
        self._has_next = True
        self._fields = None
        self._row_count = 0
        self._data = []

    @property
    def description(self):
        return self._fields

    @property
    def rowcount(self):
        return self._row_count

    def mogrify(self, query, args=None):
        if args is not None:
            query = query % self._escape_args(args)
        return query

    def escape(self, obj):
        return escape_item(obj)

    async def _fetch_query(self, num=DEFAULT_FETCH_NUM):
        message = json.dumps({
            'id': self._id,
            'qtype': TYPE_FETCH,
            'num': num,
        })
        self._connection.send_message(message)
        response = await self._connection.get_response()
        self._check_response(response)
        return self._set_data(response)

    def _set_data(self, response):
        data = json.loads(response)
        self._fields = data['fields']
        self._row_count = data['row_count']
        self._has_next = len(data['data']) > 0
        self._data = data['data']

    # async def fetch(self, num):
    #     if not self._has_next:
    #         return
    #     data_set = await self._fetch_query(num)
    #     return [convert_data(row) for row in data_set]
    #
    # async def fetchall(self):
    #     if not self._has_next:
    #         return

    async def fetchone(self):
        if not self._has_next:
            return
        await self._fetch_query(1)
        return convert_data(self._data[0])

    async def execute(self, query, args=None):
        self._has_next = True
        query = self.mogrify(query, args)
        await self._query(query)

    def _escape_args(self, args):
        if isinstance(args, (tuple, list)):
            return tuple(self.escape(arg) for arg in args)
        elif isinstance(args, dict):
            return dict((key, self.escape(val)) for (key, val) in args.items())
        else:
            return self.escape(args)

    async def _query(self, query):
        message = json.dumps({
            'id': self._id,
            'qtype': TYPE_QUERY,
            'query': query
        })
        self._connection.send_message(message)
        result = await self._connection.get_response()
        self._check_response(result)

    def _check_response(self, response):
        data = json.loads(response)
        if data.get('error') is not None:
            raise Exception(data['message'])

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._has_next and len(self._data) == 0:
            await self._fetch_query()
        return self._data.pop()


def main():
    pass


if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
import sys

if sys.version_info >= (3, 4):
    from xmlrpc.client import ServerProxy
    xrange = range
else:
    from xmlrpclib import ServerProxy

from petl.util.base import Table


def fromodoo(source, model, domain=None, fields=None, batch=100, raw_data=False):
    return OdooView(source, model, domain, fields, batch, raw_data)


def toodoo(tbl, source, model, batch=100, tracking_disable=False):
    it = iter(tbl)
    header = next(it)

    cnt = 0
    recs = []
    el = next(it, None)
    while el:
        recs += [el]
        cnt += 1
        el = next(it, None)
        if (not el) or (cnt >= batch):
            ret = source.execute(model, 'load', header, recs, {'tracking_disable': tracking_disable})
            print(ret)
            cnt = 0
            recs = []


class Odoo():
    _url = None
    _db = None
    _user = None
    _password = None
    _sock_common = None
    _sock_object = None
    _uid = None
    _version = None

    def __init__(self, url, db, user, password):
        self._url = url
        self._db = db
        self._user = user
        self._password = password
        self._sock_common = ServerProxy(url + '/xmlrpc/2/common')
        self._uid = self._sock_common.login(db, user, password)
        if not self._uid:
            raise Exception('Invalid username or password')
        self._version = self._sock_common.version()
        self._sock_object = ServerProxy(url + '/xmlrpc/2/object')

    def execute(self, *args):
        return self._sock_object.execute(self._db, self._uid, self._password, *args)


class OdooView(Table):
    _source = None
    _model = None
    _domain = []
    _fields = []
    _batch = None

    def __init__(self, source, model, domain=None, fields=None, batch=None, raw_data=False):
        self._source = source
        self._model = model
        self._batch = batch
        self._raw_data = raw_data
        if domain:
            self._domain = domain
        if fields:
            self._fields = fields

    def __iter__(self):
        if len(self._fields) == 0:
            f_id = self._source.execute('ir.model', 'search_read', [('model', '=', self._model)], ['id'])[0]['id']
            self._fields = [x['name'] for x in self._source.execute('ir.model.fields', 'search_read', [('model_id', '=', f_id)], ['name'])]
        if 'id' not in self._fields:
            self._fields += ['id']
        if '.id' not in self._fields:
            self._fields += ['.id']
        yield self._fields
        ids = self._source.execute(self._model, 'search', self._domain)
        for s in [ids[x:x + self._batch] for x in xrange(0, len(ids), self._batch)]:
            for rec in self._source.execute(self._model, 'export_data', s, self._fields, self._raw_data)['datas']:
                yield rec

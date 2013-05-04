import os
import json

from . import MixinSettings


class Sink(MixinSettings):
    def load_index(self):
        raise NotImplementedError()

    def save_index(self):
        raise NotImplementedError()


class JSON_Sink(Sink):
    def load_index(self):
        self.assert_has_arg('filename')
        if not os.path.exists(self.settings['filename']):
            return {}

        # read in the index, if it is cached
        with open(self.settings['filename']) as fh:
            data = json.load(fh)
        self.index = data['index']
        self.index_metadata = data['metadata']
        self.index_loaded = True

    def save_index(self):
        assert self.index_loaded
        self.assert_has_arg('filename')

        data = {
            "index": self.index,
            "metadata": self.mould_metadata()
        }
        with open(self.settings['filename'], 'w') as fh:
            json.dump(data, fh, indent=4)


from collections import defaultdict


class SearchIndex(object):
    def __init__(self, identifier, index=None):
        self.identifier = identifier
        self.non_json_index = index if type(index) == defaultdict else None
        self.json_index = json.dumps(index) if type(index) == dict else index

    @property
    def index(self):
        if not self.non_json_index:
            self.non_json_index = json.loads(self.json_index)
            return self.non_json_index
        else:
            return self.non_json_index

    @index.setter
    def index_setter(self, index):
        if type(index) == dict:
            self.non_json_index = index
        else:
            self.non_json_index = json.loads(index)
            self.json_index = index

    @classmethod
    def create(*args):
        return SearchIndex(*args)

    @classmethod
    def all(self, cursor):
        query = 'SELECT * FROM SearchIndex'
        cursor.execute(query)
        all_m = cursor.fetchall()

        index_models = [SearchIndex(*q) for q in all_m]
        return index_models


def insert(to_insert: dict, conn):
    # jsonify appropriately
    to_insert = [
        (key, json.dumps(value))
        for key, value in to_insert.items()
    ]

    cursor = conn.cursor()
    cursor.executemany(
        'INSERT INTO SearchIndex VALUES (?, ?)',
        to_insert)
    conn.commit()

import sqlite3


class DatabaseSink(Sink):
    def _setup_sqlite(self):
        self.assert_has_arg('database_file')
        database_file = self.settings['database_file']

        self.conn = sqlite3.connect(database_file)
        self.create_table(if_exists=False)

    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()

    def create_table(self, if_exists=False):
        if if_exists:
            self.conn.execute('DROP TABLE IF EXISTS SearchIndex')
        # ridiculous ugly, but w/e
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS SearchIndex (
                identifier TEXT NOT NULL,
                index_dict TEXT NOT NULL,
                PRIMARY KEY(identifier)
            );""")
        self.conn.commit()

    def load_index(self):
        cursor = self.conn.cursor()
        # read in the index, if it is cached
        index_models = SearchIndex.all(cursor)

        # reformat index models into usuable format
        for model in index_models:
            self.index[model.identifier] = model.index

        self.index_loaded = True

    def save_index(self):
        assert self.index_loaded
        insert(self.index, self.conn)

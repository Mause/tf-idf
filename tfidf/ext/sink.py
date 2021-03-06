import os
import json
import sqlite3

from collections import defaultdict

__all__ = ['Sink', 'JSON_Sink', 'DatabaseSink']

_types = ['db', 'json']


class Sink(object):
    "simple template for Sink object"
    def load_index(self):
        raise NotImplementedError()

    def save_index(self, tfidf_object):
        raise NotImplementedError()


class JSON_Sink(Sink):
    def __init__(self, index_filename):
        self.index_filename = index_filename

    def load_index(self):
        index_filename = os.path.abspath(self.index_filename)

        if os.path.exists(index_filename):

            # read in the index, if it is cached
            with open(index_filename) as fh:
                data = json.load(fh)

            index = data['index']
            metadata = data['metadata']
        else:
            # if the index does not yet exist
            index, metadata = {}, {}
        return index, metadata

    def save_index(self, index, metadata):
        data = {
            "index": index,
            "metadata": metadata
        }
        with open(self.index_filename, 'w') as fh:
            json.dump(data, fh, indent=4)


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

    @classmethod
    def insert(cls, to_insert: dict, conn):
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


class DatabaseSink(Sink):
    def __init__(self, database_filename):
        database_filename = os.path.abspath(database_filename)

        self.conn = sqlite3.connect(database_filename)
        self.create_table(if_exists=False)

    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()

    def create_table(self, if_exists=False):
        if if_exists:
            self.conn.execute('DROP TABLE IF EXISTS SearchIndex;')

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
        index = defaultdict(dict)

        # reformat index models into usuable format
        for model in index_models:
            index[model.identifier] = model.index

        return index, {}

    def save_index(self):
        assert self.tfidf_object.index_loaded
        SearchIndex.insert(self.tfidf_object.index, self.conn)

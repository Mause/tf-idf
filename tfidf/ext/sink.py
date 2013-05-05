import os
import json
import sqlite3

from . import MixinSettings

from collections import defaultdict

_types = ['db', 'json']


def filesize(filename):
    bytes = os.stat(filename).st_size
    kilobytes = bytes / 1024
    megabytes = kilobytes / 1024
    return megabytes


class Sink(MixinSettings):
    def load_index(self):
        raise NotImplementedError()

    def save_index(self, tfidf_object):
        raise NotImplementedError()


class JSON_Sink(Sink):
    def load_index(self):
        self.assert_has_arg('index_filename')
        index_filename = os.path.abspath(self.settings['index_filename'])

        if os.path.exists(index_filename):
            self.tfidf_object.index_size = filesize(index_filename)

            # read in the index, if it is cached
            with open(index_filename) as fh:
                data = json.load(fh)

            self.tfidf_object.index = data['index']
            self.tfidf_object.index_metadata = data['metadata']
        else:
            # if the index does not yet exist
            self.tfidf_object.index = {}
        self.tfidf_object.index_loaded = True

    def save_index(self, tfidf_object):
        assert tfidf_object.index_loaded
        self.assert_has_arg('index_filename')

        data = {
            "index": tfidf_object.index,
            "metadata": tfidf_object.mould_metadata()
        }
        with open(self.settings['index_filename'], 'w') as fh:
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
    def _setup_sqlite(self):
        self.assert_has_arg('database_filename')
        database_filename = os.path.abspath(self.settings['database_filename'])

        self.conn = sqlite3.connect(database_filename)
        self.create_table(if_exists=False)

        self.tfidf_object.index_size = filesize(database_filename)

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
            self.tfidf_object.index[model.identifier] = model.index

        self.tfidf_object.index_loaded = True

    def save_index(self):
        assert self.tfidf_object.index_loaded
        SearchIndex.insert(self.tfidf_object.index, self.conn)

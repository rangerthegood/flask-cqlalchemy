# -*- coding: utf-8 -*-
"""
flask_cqlalchemy

:copyright: (c) 2015 by George Thomas
:license: BSD, see LICENCSE for more details

"""
from cassandra.cqlengine import connection
from cassandra.cqlengine.management import sync_table, create_keyspace_simple
from cassandra.cqlengine import columns
from cassandra.cqlengine import models

try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack


class CQLAlchemy(object):
    """The CQLAlchemy class. All CQLEngine methods are available as methods of
    Model or columns attribute in this class.
    No teardown method is available as connections are costly and once made are
    ideally not disconnected.
    """

    def __init__(self, app=None):
        """Constructor for the class"""
        self.columns = columns
        self.Model = models.Model
        self.app = app
        self.sync_table = sync_table
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Bind the CQLAlchemy object to the app.

        This method set all the config options for the connection to
        the Cassandra cluster and creates a connection at startup.
        """
        self._hosts_ = app.config['CASSANDRA_HOSTS']
        self._keyspace_ = app.config['CASSANDRA_KEYSPACE']
        consistency = app.config.get('CASSANDRA_CONSISTENCY', 1)
        lazy_connect = app.config.get('CASSANDRA_LAZY_CONNECT', False)
        retry_connect = app.config.get('CASSANDRA_RETRY_CONNECT', False)
        setup_kwargs = app.config.get('CASSANDRA_SETUP_KWARGS', {})

        # Create a keyspace with a replication factor of 2
        # If the keyspace already exists, it will not be modified
        if not self._hosts_ and self._keyspace_:
            raise NoConfig("No Configuration options defined. At least CASSANDRA_HOSTS and CASSANDRA_CONSISTENCY must be supplied")
        connection.setup(self._hosts_,
                         self._keyspace_,
                         consistency=consistency,
                         lazy_connect=lazy_connect,
                         retry_connect=retry_connect,
                         **setup_kwargs)

    def create_all(self):
        """Creates all the keyspaces and tables necessary for the app.
        If run from a shell, all defined models must be imported before
        this method is called
        """
        create_keyspace_simple(self._keyspace_, 2)
        models = [cls for cls in self.Model.__subclasses__()]
        for model in models:
            sync_table(model)

    def sync_db(self):
        """Sync all defined tables. All defined models must be imported before
        this method is called
        """
        models = [cls for cls in self.Model.__subclasses__()]
        for model in models:
            sync_table(model)

    def set_keyspace(self, keyspace_name):
        """ Changes keyspace for the current session if keyspace_name is
        supplied. Ideally sessions exist for the entire duration of the
        application. So if the change in keyspace is meant to be temporary,
        this method must be called again without any arguments
        """
        if not keyspace_name:
            keyspace_name = self._default_keyspace_
        models.DEFAULT_KEYSPACE = keyspace_name
        self._keyspace_ = keyspace_name


class NoConfig(Exception):
    """ Raised when CASSANDRA_HOSTS or CASSANDRA_KEYSPACE is not defined"""
    pass
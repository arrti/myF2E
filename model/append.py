#!/usr/bin/env python
# coding=utf-8
#
# Copyright 2012 F2E.im
# Do have a faith in what you're doing.
# Make your life a story worth telling.

import time
from lib.query import Query

class AppendModel(Query):
    def __init__(self, db):
        self.db = db
        self.table_name = "append"
        super(AppendModel, self).__init__()

    def get_topic_append_by_topic_id(self, topic_id):
        where = "topic_id = %s" % topic_id
        order = "id ASC"
        field = "append.*"
        return self.where(where).order(order).select()

    def add_new_append(self, append_info):
        return self.data(append_info).add()

    def get_topic_append_count(self, topic_id):
        where = "topic_id = %s" % topic_id
        return self.where(where).count()



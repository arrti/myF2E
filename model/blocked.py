#!/usr/bin/env python
# coding=utf-8
#
# Copyright 2012 F2E.im
# Do have a faith in what you're doing.
# Make your life a story worth telling.

import time
from lib.query import Query

class BlockedModel(Query):
    def __init__(self, db):
        self.db = db
        self.table_name = "blocked"
        super(BlockedModel, self).__init__()

    def get_blocked_topic_id(self, uid = None):
        if not uid:
            where = "involved_topic_id IS NOT NULL AND status = 1"
        else:
            where = "involved_topic_id IS NOT NULL AND (trigger_user_id = %s OR status = 1)" % uid
        field = "involved_topic_id"
        return self.where(where).field(field).select()

    def get_blocked_user_id(self, uid = None):
        if not uid:
            where = "involved_user_id IS NOT NULL AND status = 1"
        else:
            where = "involved_user_id IS NOT NULL AND (trigger_user_id = %s OR status = 1)" % uid
        field = "involved_user_id"
        return self.where(where).field(field).select()

    def get_user_blocked_topic_by_involved_topic_id_and_trigger_user_id(self, involved_topic_id, trigger_user_id):
        where = "involved_topic_id = %s AND (trigger_user_id = %s OR status = 1)" % (involved_topic_id, trigger_user_id)
        return self.where(where).find()

    def get_user_blocked_user_by_involved_user_id_and_trigger_user_id(self, involved_user_id, trigger_user_id):
        where = "involved_user_id = %s AND (trigger_user_id = %s OR status = 1)" % (involved_user_id, trigger_user_id)
        return self.where(where).find()

    def add_new_blocked(self, blocked_info):
        return self.data(blocked_info).add()


    def delete_blocked_by_involved_user_id_and_trigger_user_id(self, involved_user_id, trigger_user_id):
        where = "involved_user_id = %s AND trigger_user_id = %s" % (involved_user_id, trigger_user_id)
        return self.where(where).delete()


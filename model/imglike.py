#!/usr/bin/env python
# coding=utf-8
#
# Copyright 2012 F2E.im
# Do have a faith in what you're doing.
# Make your life a story worth telling.

import time
from lib.query import Query

class ImglikeModel(Query):
    def __init__(self, db):
        self.db = db
        self.table_name = "imglike"
        super(ImglikeModel, self).__init__()

    def get_image_like_by_image_id_and_trigger_user_id(self, image_id, trigger_user_id):
        where = "involved_image_id = %s AND trigger_user_id = %s" % (image_id, trigger_user_id)
        return self.where(where).find()

    def add_new_image_like(self, image_like_info):
        return self.data(image_like_info).add()


    def delete_image_like_by_image_id_and_trigger_user_id(self, image_id, trigger_user_id):
        where = "involved_image_id = %s AND trigger_user_id = %s" % (image_id, trigger_user_id)
        return self.where(where).delete()


#!/usr/bin/env python
# coding=utf-8
#
# Copyright 2012 F2E.im
# Do have a faith in what you're doing.
# Make your life a story worth telling.

import time
from lib.query import Query

class ImageModel(Query):
    def __init__(self, db):
        self.db = db
        self.table_name = "image"
        super(ImageModel, self).__init__()

    def get_all_waterfall(self, num = 9, current_page = 1):
        where = "image.waterfall = 1"
        join = "LEFT JOIN user ON image.owner_id = user.uid "
        order = "updated DESC, created DESC, id DESC"
        field = "image.*, \
                image.name as image_name, \
                image.description as image_desp, \
                user.username as owner_username"
        return self.where(where).order(order).join(join).field(field).pages(current_page = current_page, list_rows = num)

    def get_image_by_image_id(self, image_id):
        where = "image.id = %s" % image_id
        return self.where(where).find()

    def get_user_all_iamges_count(self, uid):
        where = "owner_id = %s" % uid
        return self.where(where).count()

    def get_all_images_count(self):
        return self.count()

    def get_user_all_images(self, uid, num = 6, current_page = 1):
        where = "owner_id = %s" % uid
        order = "id DESC"
        field = "*, name as image_name, description as image_desp"
        return self.where(where).order(order).field(field).pages(current_page = current_page, list_rows = num)

    def get_user_all_images_and_likes_count(self, uid, num = 6, current_page = 1):
        where = "image.owner_id = %s" % uid
        join = "LEFT JOIN imglike ON image.id = imglike.involved_image_id"
        order = "image.id DESC"
        field = "image.*, image.name as image_name, image.description as image_desp, COUNT(imglike.involved_image_id) as likes_count"
        group = "image.id"
        return self.where(where).order(order).join(join).group(group).field(field).pages(current_page = current_page, list_rows = num)

    def add_new_image(self, image_info):
        return self.data(image_info).add()

    def update_image_by_image_id(self, image_id, image_info):
        where = "image.id = %s" % image_id
        return self.where(where).data(image_info).save()

    def delete_image_by_image_id(self, image_id):
        where = "image.id = %s" % image_id
        return self.where(where).delete()


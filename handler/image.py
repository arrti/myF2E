#!/usr/bin/env python
# coding=utf-8
#
# Copyright 2012 F2E.im
# Do have a faith in what you're doing.
# Make your life a story worth telling.

import uuid
import hashlib
from PIL import Image
import StringIO
import time
import json
import re
import urllib2
import tornado.web
import lib.jsonp
import pprint
import math
import datetime
import glob
import os
from qiniu import Auth
from qiniu import put_data
from qiniu import put_file
from qiniu import etag

from base import *
from lib.variables import *
from form.image import *
from lib.variables import gen_random
from lib.xss import XssCleaner
from lib.utils import find_mentions

#qiniu cloud
access_key = 'your access_key'
secret_key = 'your secret_key'
bucket_name = 'lyour bucket_name'
bucket_domain = "your bucket_domain"

class WaterFallHandler(BaseHandler):
    def get(self, template_variables = {}):
        user_info = self.current_user
        template_variables["user_info"] = user_info
        if(user_info):
            template_variables["user_info"]["counter"] = {
                "topics": self.topic_model.get_user_all_topics_count(user_info["uid"]),
                "replies": self.reply_model.get_user_all_replies_count(user_info["uid"]),
                "favorites": self.favorite_model.get_user_favorite_count(user_info["uid"]),
            }

            template_variables["notifications_count"] = self.notification_model.get_user_unread_notification_count(user_info["uid"]);

        '''images = {}
        list = []
        paths = glob.glob(r"static/waterfall/*.jpg")
        for f in paths:
            info = {}
            info["owner_username"] = "dxc"
            info["image_name"] = f.split("/")[-1]
            info["image_desp"] = "你好 旅行者"
            list.append(info)
        images["list"] = list'''
        template_variables["waterfall"] = self.image_model.get_all_waterfall()
        template_variables["gen_random"] = gen_random
        template_variables["active_page"] = "waterfall"
        self.render("page/waterfall.html", **template_variables)

class SettingAlbumHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, template_variables = {}):
        user_info = self.get_current_user()
        template_variables["user_info"] = user_info

        '''images = {}
        list = []
        paths = glob.glob(r"static/waterfall/*.jpg")
        for f in paths[0:6]:
            info = {}
            info["owner_username"] = "dxc"
            info["image_name"] = f.split("/")[-1]
            info["image_desp"] = "你好 旅行者"
            list.append(info)
        images["list"] = list'''
        template_variables["album"] = self.image_model.get_user_all_images_and_likes_count(user_info["uid"])
        #template_variables["ceshi"] = self.image_model.get_user_all_images_and_likes_count(user_info["uid"])
        template_variables["image_count"] = self.image_model.get_user_all_iamges_count(user_info["uid"])
        template_variables["gen_random"] = gen_random
        self.render("user/setting_album.html", **template_variables)

    @tornado.web.authenticated
    def post(self, template_variables = {}):
        template_variables = {}


        if(not "image" in self.request.files):
            form = UpdateDescriptionForm(self)
            if not form.validate():
                self.get({"errors": form.errors})
                return
            image_info = {
                "description": form.description.data,
                "updated": time.strftime('%Y-%m-%d %H:%M:%S'),
            }
            image_id = form.imgid.data
            image_id = self.image_model.update_image_by_image_id(image_id, image_info)
            template_variables["success_message"] = [u"照片描述更新成功"]
            self.get(template_variables)
            return

        form = SettingAlbumForm(self)
        if not form.validate():
            self.get({"errors": form.errors})
            return

        user_info = self.current_user
        user_id = user_info["uid"]
        image_name = "%s" % uuid.uuid1()
        image_raw = self.request.files["image"][0]["body"]
        if len(image_raw) > 5*1024*1024: #4MB
            template_variables["errors"] = {}
            template_variables["errors"]["invalid_size"] = [u"照片应小于5MB，当前为%dMB" % len(image_raw)/1024/1024]
            self.get(template_variables)
            return
        image_buffer = StringIO.StringIO(image_raw)
        try:
            image = Image.open(image_buffer)
        except IOError:
            template_variables["errors"] = {}
            template_variables["errors"]["invalid_file"] = [u"照片无法打开"]
            self.get(template_variables)
            return

        image.save("./static/waterfall/%s.%s" % (image_name, image.format), image.format)
        image_info = {
            "name": "%s.%s" % (image_name, image.format),
            "description": form.description.data,
            "owner_id": user_info["uid"],
            "created": time.strftime('%Y-%m-%d %H:%M:%S'),
            "updated": time.strftime('%Y-%m-%d %H:%M:%S'),
            "waterfall": 0,
        }
        image_id = self.image_model.add_new_image(image_info)
        template_variables["success_message"] = [u"照片上传成功"]
        self.get(template_variables)

class SetWaterFallHandler(BaseHandler):
    def get(self, template_variables = {}):
        image_id = int(self.get_argument("image_id"))
        image_info = self.image_model.get_image_by_image_id(image_id)

        if not self.current_user:
            self.write(lib.jsonp.print_JSON({
                "success": 0,
                "message": "user_not_login",
            }))
            return

        if not image_info:
            self.write(lib.jsonp.print_JSON({
                "success": 0,
                "message": "image_not_exist",
            }))
            return

        if self.current_user["uid"] != image_info["owner_id"]:
            self.write(lib.jsonp.print_JSON({
                "success": 0,
                "message": "can_not_set_not_your_image",
            }))
            return

        if image_info["waterfall"] == 1:
            self.write(lib.jsonp.print_JSON({
                "success": 0,
                "message": "already_seted",
            }))
            return

        image_info = {}
        image_info["waterfall"] = 1
        image_info["updated"] = time.strftime('%Y-%m-%d %H:%M:%S')
        self.image_model.update_image_by_image_id(image_id, image_info)

        self.write(lib.jsonp.print_JSON({
            "success": 1,
            "message": "set_waterfall_success",
        }))

class ResetWaterFallHandler(BaseHandler):
    def get(self, template_variables = {}):
        image_id = int(self.get_argument("image_id"))
        image_info = self.image_model.get_image_by_image_id(image_id)

        if not self.current_user:
            self.write(lib.jsonp.print_JSON({
                "success": 0,
                "message": "user_not_login",
            }))
            return

        if not image_info:
            self.write(lib.jsonp.print_JSON({
                "success": 0,
                "message": "image_not_exist",
            }))
            return

        if self.current_user["uid"] != image_info["owner_id"]:
            self.write(lib.jsonp.print_JSON({
                "success": 0,
                "message": "can_not_set_not_your_image",
            }))
            return

        self.image_model.delete_image_by_image_id(image_id)

        self.write(lib.jsonp.print_JSON({
            "success": 1,
            "message": "delete_image_success",
        }))

class DeleteImageHandler(BaseHandler):
    def get(self, template_variables = {}):
        image_id = int(self.get_argument("image_id"))
        image_info = self.image_model.get_image_by_image_id(image_id)

        if not self.current_user:
            self.write(lib.jsonp.print_JSON({
                "success": 0,
                "message": "user_not_login",
            }))
            return

        if not image_info:
            self.write(lib.jsonp.print_JSON({
                "success": 0,
                "message": "image_not_exist",
            }))
            return

        if self.current_user["uid"] != image_info["owner_id"]:
            self.write(lib.jsonp.print_JSON({
                "success": 0,
                "message": "can_not_delete_not_your_image",
            }))
            return

        self.image_model.delete_image_by_image_id(image_id)
        image_path = "./static/waterfall/%s" % image_info["name"]
        os.remove(image_path)

        self.write(lib.jsonp.print_JSON({
            "success": 1,
            "message": "delete_image_success",
        }))

class LikeImageHandler(BaseHandler):
    def get(self, template_variables = {}):
        image_id = int(self.get_argument("image_id"))
        image_info = self.image_model.get_image_by_image_id(image_id)
        image_like_info = self.image_like_model.get_image_like_by_image_id_and_trigger_user_id(image_id, self.current_user["uid"])

        if not self.current_user:
            self.write(lib.jsonp.print_JSON({
                "success": 0,
                "message": "user_not_login",
            }))
            return

        if not image_info:
            self.write(lib.jsonp.print_JSON({
                "success": 0,
                "message": "image_not_exist",
            }))
            return

        if image_like_info:
            self.write(lib.jsonp.print_JSON({
                "success": 0,
                "message": "image_already_liked",
            }))
            return

        if self.current_user["uid"] == image_info["owner_id"]:
            self.write(lib.jsonp.print_JSON({
                "success": 0,
                "message": "can_not_like_your_image",
            }))
            return

        image_like_info = {
            "owner_user_id": image_info["owner_id"],
            "involved_image_id": image_id,
            "trigger_user_id": self.current_user["uid"],
            "occurrence_time": time.strftime('%Y-%m-%d %H:%M:%S'),
        }
        image_id = self.image_like_model.add_new_image_like(image_like_info)

        self.write(lib.jsonp.print_JSON({
            "success": 1,
            "message": "image_like_success",
        }))

class UnlikeImageHandler(BaseHandler):
    def get(self, template_variables = {}):
        image_id = int(self.get_argument("image_id"))
        image_info = self.image_model.get_image_by_image_id(image_id)
        image_like_info = self.image_like_model.get_image_like_by_image_id_and_trigger_user_id(image_id, self.current_user["uid"])

        if not self.current_user:
            self.write(lib.jsonp.print_JSON({
                "success": 0,
                "message": "user_not_login",
            }))
            return

        if not image_info:
            self.write(lib.jsonp.print_JSON({
                "success": 0,
                "message": "image_not_exist",
            }))
            return

        if not image_like_info:
            self.write(lib.jsonp.print_JSON({
                "success": 0,
                "message": "image_not_liked",
            }))
            return

        image_id = self.image_like_model.delete_image_like_by_image_id_and_trigger_user_id(image_id, self.current_user["uid"])

        self.write(lib.jsonp.print_JSON({
            "success": 1,
            "message": "image_unlike_success",
        }))

class QiNiuHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self, template_variables = {}):
        template_variables = {}

        if(not "image" in self.request.files):
            self.write(lib.jsonp.print_JSON({
                "success": 0,
                "message": "image_not_exist",
            }))
            return
        re_image = re.compile(r'.*\.(jpg|jpeg|gif|png)$')
        image_type = re_image.match(self.request.files["image"][0]["filename"].lower())
        if not image_type:
            self.write(lib.jsonp.print_JSON({
                "success": 0,
                "message": "invalid_image_type",
            }))
            return

        image_raw = self.request.files["image"][0]["body"]
        if len(image_raw) > 2*1024*1024: #2MB
            self.write(lib.jsonp.print_JSON({
                "success": 0,
                "message": "image_error_size",
            }))
            return
        image_buffer = StringIO.StringIO(image_raw)
        try:
            image = Image.open(image_buffer)
        except IOError:
            self.write(lib.jsonp.print_JSON({
                "success": 0,
                "message": "invalid_image",
            }))
            return

        q = Auth(access_key, secret_key)
        key = "%s.%s" % (uuid.uuid1(), image_type.group(1))
        mime_type = "text/plain"
        params = {'x:a': 'a'}

        token = q.upload_token(bucket_name, key)
        ret, info = put_data(token, key, image_raw, mime_type=mime_type, check_crc=True)
        if ret['key'] != key:
            self.write(lib.jsonp.print_JSON({
                "success": 0,
                "message": "image_insert_failed",
            }))
            return

        self.write(lib.jsonp.print_JSON({
                "success": 1,
                "message": bucket_domain + "/" + key,#image external link
            }))


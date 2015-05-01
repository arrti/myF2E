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

from base import *
from lib.variables import *
from form.topic import *
from lib.variables import gen_random
from lib.xss import XssCleaner
from lib.utils import find_mentions

class IndexHandler(BaseHandler):
    def get(self, template_variables = {}):
        user_info = self.current_user
        page = int(self.get_argument("p", "1"))
        template_variables["user_info"] = user_info
        user_id = None
        if(user_info):
            template_variables["user_info"]["counter"] = {
                "topics": self.topic_model.get_user_all_topics_count(user_info["uid"]),
                "replies": self.reply_model.get_user_all_replies_count(user_info["uid"]),
                "favorites": self.favorite_model.get_user_favorite_count(user_info["uid"]),
            }

            template_variables["notifications_count"] = self.notification_model.get_user_unread_notification_count(user_info["uid"]);
            user_id = user_info['uid']
        template_variables["status_counter"] = {
            "users": self.user_model.get_all_users_count(),
            "nodes": self.node_model.get_all_nodes_count(),
            "topics": self.topic_model.get_all_topics_count(),
            "replies": self.reply_model.get_all_replies_count(),
        }

        blocked_topic_list = self.blocked_model.get_blocked_topic_id(user_id)
        if not blocked_topic_list:
            blocked_topic = [-1,-2]# no blocked, all invalid topic id > 0, this will block no topic
        else:
            blocked_topic = [-1]#to ensure that sql "in ()" have at least 2 items, only 1 item in tuple will be (22,), the ',' is wrong in sql
            for row in blocked_topic_list:
                blocked_topic.append(row['involved_topic_id'])
        blocked_topic = re.sub('L', '', str(tuple(blocked_topic)))#int type from mysql  convert python long type like 22L, so use re remove 'L'
        blocked_user_list = self.blocked_model.get_blocked_user_id(user_id)
        if not blocked_user_list:
            blocked_user = [-1,-2]# no blocked, all invalid user id > 0, this will block no user
        else:
            blocked_user = [-1]
            for row in blocked_user_list:
                blocked_user.append(row['involved_user_id'])
        blocked_user = re.sub('L', '', str(tuple(blocked_user)))
        template_variables["topics"] = self.topic_model.get_all_not_blocked_topics(current_page = page, blocked_user = blocked_user, blocked_topic = blocked_topic)
        template_variables["planes"] = self.plane_model.get_all_planes_with_nodes()
        template_variables["hot_nodes"] = self.node_model.get_all_hot_nodes()
        template_variables["active_page"] = "topic"
        template_variables["gen_random"] = gen_random
        self.render("topic/topics.html", **template_variables)

class NodeTopicsHandler(BaseHandler):
    def get(self, node_slug, template_variables = {}):
        user_info = self.current_user
        page = int(self.get_argument("p", "1"))
        template_variables["user_info"] = user_info
        if(user_info):
            template_variables["user_info"]["counter"] = {
                "topics": self.topic_model.get_user_all_topics_count(user_info["uid"]),
                "replies": self.reply_model.get_user_all_replies_count(user_info["uid"]),
                "favorites": self.favorite_model.get_user_favorite_count(user_info["uid"]),
            }

            template_variables["notifications_count"] = self.notification_model.get_user_unread_notification_count(user_info["uid"]);

        template_variables["topics"] = self.topic_model.get_all_topics_by_node_slug(current_page = page, node_slug = node_slug)
        template_variables["node"] = self.node_model.get_node_by_node_slug(node_slug)
        template_variables["active_page"] = "topic"
        template_variables["gen_random"] = gen_random
        self.render("topic/node_topics.html", **template_variables)

class ViewHandler(BaseHandler):
    def get(self, topic_id, template_variables = {}):
        user_info = self.current_user
        page = int(self.get_argument("p", "1"))
        user_info = self.get_current_user()
        template_variables["user_info"] = user_info
        user_id = None
        if(user_info):
            template_variables["user_info"]["counter"] = {
                "topics": self.topic_model.get_user_all_topics_count(user_info["uid"]),
                "replies": self.reply_model.get_user_all_replies_count(user_info["uid"]),
                "favorites": self.favorite_model.get_user_favorite_count(user_info["uid"]),
            }

            template_variables["notifications_count"] = self.notification_model.get_user_unread_notification_count(user_info["uid"]);
            template_variables["topic_favorited"] = self.favorite_model.get_favorite_by_topic_id_and_owner_user_id(topic_id, user_info["uid"]);
            user_id = user_info['uid']
        template_variables["gen_random"] = gen_random
        template_variables["topic"] = self.topic_model.get_topic_by_topic_id(topic_id)
        template_variables["appends"] = self.append_model.get_topic_append_by_topic_id(topic_id)
        # check reply count and cal current_page if `p` not given
        reply_num = 106
        reply_count = template_variables["topic"]["reply_count"]
        reply_last_page = (reply_count / reply_num + (reply_count % reply_num and 1)) or 1
        page = int(self.get_argument("p", reply_last_page))
        template_variables["reply_num"] = reply_num
        template_variables["current_page"] = page

        blocked_user_list = self.blocked_model.get_blocked_user_id(user_id)
        if not blocked_user_list:
            blocked_user = [-1,-2]# no blocked, all invalid user id > 0, this will block no user
        else:
            blocked_user = [-1]
            for row in blocked_user_list:
                blocked_user.append(row['involved_user_id'])
        blocked_user = re.sub('L', '', str(tuple(blocked_user)))
        template_variables["replies"] = self.reply_model.get_all_not_blocked_replies_by_topic_id(topic_id, current_page = page, num = reply_num, blocked_user = blocked_user)
        template_variables["active_page"] = "topic"

        # update topic reply_count and hits

        self.topic_model.update_topic_by_topic_id(topic_id, {
            "reply_count": template_variables["replies"]["page"]["total"],
            "hits": (template_variables["topic"]["hits"] or 0) + 1,
        })

        self.render("topic/view.html", **template_variables)

    @tornado.web.authenticated
    def post(self, template_variables = {}):
        template_variables = {}

        # validate the fields

        form = ReplyForm(self)

        if not form.validate():
            self.get(form.tid.data, {"errors": form.errors})
            return

        # continue while validate succeed

        topic_info = self.topic_model.get_topic_by_topic_id(form.tid.data)
        replied_info = self.reply_model.get_user_last_reply_by_topic_id(self.current_user["uid"], form.tid.data)

        if(not topic_info):
            template_variables["errors"] = {}
            template_variables["errors"]["invalid_topic_info"] = [u"要回复的帖子不存在"]
            self.get(form.tid.data, template_variables)
            return

        if(replied_info):
            #last_replied_fingerprint = hashlib.sha1(str(replied_info.topic_id) + str(replied_info.author_id) + replied_info.content).hexdigest()
            #new_replied_fingerprint = hashlib.sha1(str(form.tid.data) + str(self.current_user["uid"]) + form.content.data).hexdigest()

            last_replied_fingerprint = hashlib_sha1(str(replied_info.topic_id) + str(replied_info.author_id) + replied_info.content)
            new_replied_fingerprint = hashlib_sha1(str(form.tid.data) + str(self.current_user["uid"]) + form.content.data)

            if last_replied_fingerprint == new_replied_fingerprint:
                template_variables["errors"] = {}
                template_variables["errors"]["duplicated_reply"] = [u"回复重复提交"]
                self.get(form.tid.data, template_variables)
                return
        
        reply_info = {
            "author_id": self.current_user["uid"],
            "topic_id": form.tid.data,
            # "content": XssCleaner().strip(form.content.data),
            "content": form.content.data,
            "created": time.strftime('%Y-%m-%d %H:%M:%S'),
        }

        reply_id = self.reply_model.add_new_reply(reply_info)

        # update topic last_replied_by and last_replied_time

        self.topic_model.update_topic_by_topic_id(form.tid.data, {
            "last_replied_by": self.current_user["uid"],
            "last_replied_time": time.strftime('%Y-%m-%d %H:%M:%S'),
            "last_touched": time.strftime('%Y-%m-%d %H:%M:%S'),
        })

        # create reply notification

        if not self.current_user["uid"] == topic_info["author_id"]:
            self.notification_model.add_new_notification({
                "trigger_user_id": self.current_user["uid"],
                "involved_type": 1, # 0: mention, 1: reply
                "involved_user_id": topic_info["author_id"],
                "involved_topic_id": form.tid.data,
                "content": form.content.data,
                "status": 0,
                "occurrence_time": time.strftime('%Y-%m-%d %H:%M:%S'),
            })

        # create @username notification

        for username in set(find_mentions(form.content.data)):
            mentioned_user = self.user_model.get_user_by_username(username)

            if not mentioned_user:
                continue

            if mentioned_user["uid"] == self.current_user["uid"]:
                continue

            if mentioned_user["uid"] == topic_info["author_id"]:
                continue

            self.notification_model.add_new_notification({
                "trigger_user_id": self.current_user["uid"],
                "involved_type": 0, # 0: mention, 1: reply
                "involved_user_id": mentioned_user["uid"],
                "involved_topic_id": form.tid.data,
                "content": form.content.data,
                "status": 0,
                "occurrence_time": time.strftime('%Y-%m-%d %H:%M:%S'),
            })

        # update reputation of topic author
        if not self.current_user["uid"] == topic_info["author_id"] and not replied_info:
            topic_time_diff = datetime.datetime.now() - topic_info["created"]
            reputation = topic_info["author_reputation"] or 0
            reputation = reputation + 2 * math.log(self.current_user["reputation"] or 0 + topic_time_diff.days + 10, 10)
            self.user_model.set_user_base_info_by_uid(topic_info["author_id"], {"reputation": reputation})

        # self.get(form.tid.data)
        self.redirect("/t/%s#reply%s" % (form.tid.data, topic_info["reply_count"] + 1))

class CreateHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, node_slug = None, template_variables = {}):
        user_info = self.current_user
        template_variables["user_info"] = user_info
        template_variables["user_info"]["counter"] = {
            "topics": self.topic_model.get_user_all_topics_count(user_info["uid"]),
            "replies": self.reply_model.get_user_all_replies_count(user_info["uid"]),
            "favorites": self.favorite_model.get_user_favorite_count(user_info["uid"]),
        }

        template_variables["notifications_count"] = self.notification_model.get_user_unread_notification_count(user_info["uid"]);
        template_variables["gen_random"] = gen_random
        template_variables["node_slug"] = node_slug
        template_variables["active_page"] = "topic"
        self.render("topic/create.html", **template_variables)

    @tornado.web.authenticated
    def post(self, node_slug = None, template_variables = {}):
        template_variables = {}

        # validate the fields

        form = CreateForm(self)

        if not form.validate():
            self.get(node_slug, {"errors": form.errors})
            return

        # continue while validate succeed

        node = self.node_model.get_node_by_node_slug(node_slug)
        last_created = self.topic_model.get_user_last_created_topic(self.current_user["uid"])

        if last_created:
            #last_created_fingerprint = hashlib.sha1(last_created.title + last_created.content + str(last_created.node_id)).hexdigest()
            #new_created_fingerprint = hashlib.sha1(form.title.data + form.content.data + str(node["id"])).hexdigest()

            last_created_fingerprint = hashlib_sha1(last_created.title + last_created.content + str(last_created.node_id))
            new_created_fingerprint = hashlib_sha1(form.title.data + form.content.data + str(node["id"]))

            if last_created_fingerprint == new_created_fingerprint:
                template_variables["errors"] = {}
                template_variables["errors"]["duplicated_topic"] = [u"帖子重复提交"]
                self.get(node_slug, template_variables)
                return
        
        topic_info = {
            "author_id": self.current_user["uid"],
            "title": form.title.data,
            # "content": XssCleaner().strip(form.content.data),
            "content": form.content.data,
            "node_id": node["id"],
            "created": time.strftime('%Y-%m-%d %H:%M:%S'),
            "reply_count": 0,
            "last_touched": time.strftime('%Y-%m-%d %H:%M:%S'),
        }

        reply_id = self.topic_model.add_new_topic(topic_info)

        # update reputation of topic author
        reputation = self.current_user["reputation"] or 0
        reputation = reputation - 5
        reputation = 0 if reputation < 0 else reputation
        self.user_model.set_user_base_info_by_uid(topic_info["author_id"], {"reputation": reputation})
        self.redirect("/")

class EditHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, topic_id, template_variables = {}):
        user_info = self.current_user
        template_variables["user_info"] = user_info
        template_variables["user_info"]["counter"] = {
            "topics": self.topic_model.get_user_all_topics_count(user_info["uid"]),
            "replies": self.reply_model.get_user_all_replies_count(user_info["uid"]),
            "favorites": self.favorite_model.get_user_favorite_count(user_info["uid"]),
        }

        template_variables["notifications_count"] = self.notification_model.get_user_unread_notification_count(user_info["uid"]);
        template_variables["topic"] = self.topic_model.get_topic_by_topic_id(topic_id)
        template_variables["gen_random"] = gen_random
        template_variables["active_page"] = "topic"
        self.render("topic/edit.html", **template_variables)

    @tornado.web.authenticated
    def post(self, topic_id, template_variables = {}):
        template_variables = {}

        # validate the fields

        form = CreateForm(self)

        if not form.validate():
            self.get(topic_id, {"errors": form.errors})
            return

        # continue while validate succeed

        topic_info = self.topic_model.get_topic_by_topic_id(topic_id)

        if(not topic_info["author_id"] == self.current_user["uid"]):
            template_variables["errors"] = {}
            template_variables["errors"]["invalid_permission"] = [u"没有权限修改该主题"]
            self.get(topic_id, template_variables)
            return

        update_topic_info = {
            "title": form.title.data,
            # "content": XssCleaner().strip(form.content.data),
            "content": form.content.data,
            "updated": time.strftime('%Y-%m-%d %H:%M:%S'),
            "last_touched": time.strftime('%Y-%m-%d %H:%M:%S'),
        }

        reply_id = self.topic_model.update_topic_by_topic_id(topic_id, update_topic_info)

        # update reputation of topic author
        reputation = topic_info["author_reputation"] or 0
        reputation = reputation - 2
        reputation = 0 if reputation < 0 else reputation
        self.user_model.set_user_base_info_by_uid(topic_info["author_id"], {"reputation": reputation})
        self.redirect("/t/%s" % topic_id)

class AppendHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, topic_id, template_variables = {}):
        user_info = self.current_user
        template_variables["user_info"] = user_info
        template_variables["user_info"]["counter"] = {
            "topics": self.topic_model.get_user_all_topics_count(user_info["uid"]),
            "replies": self.reply_model.get_user_all_replies_count(user_info["uid"]),
            "favorites": self.favorite_model.get_user_favorite_count(user_info["uid"]),
        }

        template_variables["notifications_count"] = self.notification_model.get_user_unread_notification_count(user_info["uid"]);
        template_variables["topic"] = self.topic_model.get_topic_by_topic_id(topic_id)
        template_variables["appends"] = self.append_model.get_topic_append_by_topic_id(topic_id)
        template_variables["gen_random"] = gen_random
        template_variables["active_page"] = "topic"
        self.render("topic/append.html", **template_variables)

    @tornado.web.authenticated
    def post(self, topic_id, template_variables = {}):
        template_variables = {}

        # validate the fields

        form = AppendForm(self)

        if not form.validate():
            self.get(topic_id, {"errors": form.errors})
            return

        # continue while validate succeed

        topic_info = self.topic_model.get_topic_by_topic_id(topic_id)

        if(not topic_info["author_id"] == self.current_user["uid"]):
            template_variables["errors"] = {}
            template_variables["errors"]["invalid_permission"] = [u"没有权限为该主题追加说明"]
            self.get(topic_id, template_variables)
            return
        append_content = '\n---   \n'
        append_content = append_content + form.content.data
        append_info = {
            "topic_id": topic_id,
            "author_id": self.current_user["uid"],
            "content": form.content.data,
            "created": time.strftime('%Y-%m-%d %H:%M:%S'),
        }

        update_topic_info = {
            "updated": time.strftime('%Y-%m-%d %H:%M:%S'),
            "last_touched": time.strftime('%Y-%m-%d %H:%M:%S'),
        }

        reply_id = self.topic_model.update_topic_by_topic_id(topic_id, update_topic_info)
        append_id = self.append_model.add_new_append(append_info)

        # update reputation of topic author
        reputation = topic_info["author_reputation"] or 0
        reputation = reputation - 2
        reputation = 0 if reputation < 0 else reputation
        self.user_model.set_user_base_info_by_uid(topic_info["author_id"], {"reputation": reputation})
        self.redirect("/t/%s" % topic_id)

class ProfileHandler(BaseHandler):
    def get(self, user, template_variables = {}):
        if(re.match(r'^\d+$', user)):
            user_info = self.user_model.get_user_by_uid(user)
        else:
            user_info = self.user_model.get_user_by_username(user)

        if not user_info:
            self.write_error(404)
            return

        current_user = self.current_user
        page = int(self.get_argument("p", "1"))
        template_variables["user_info"] = user_info
        if(user_info):
            template_variables["user_info"]["counter"] = {
                "topics": self.topic_model.get_user_all_topics_count(user_info["uid"]),
                "replies": self.reply_model.get_user_all_replies_count(user_info["uid"]),
                "favorites": self.favorite_model.get_user_favorite_count(user_info["uid"]),
            }

        if(current_user):
            template_variables["notifications_count"] = self.notification_model.get_user_unread_notification_count(current_user["uid"]);

        '''
        if user_info["github"]:
            github_repos = self.mc.get(str("%s_github_repos" % user_info["github"])) or json.JSONDecoder().decode(urllib2.urlopen('https://api.github.com/users/%s/repos' % user_info["github"]).read())
            self.mc.set(str("%s_github_repos" % user_info["github"]), github_repos)
            template_variables["github_repos"] = github_repos
        '''

        template_variables["topics"] = self.topic_model.get_user_all_topics(user_info["uid"], current_page = page)
        template_variables["replies"] = self.reply_model.get_user_all_replies(user_info["uid"], current_page = page)
        template_variables["gen_random"] = gen_random
        template_variables["active_page"] = "_blank"
        self.render("topic/profile.html", **template_variables)

class CardHandler(BaseHandler):
    def get(self, user, template_variables = {}):
        if(re.match(r'^\d+$', user)):
            user_info = self.user_model.get_user_by_uid(user)
        else:
            user_info = self.user_model.get_user_by_username(user)

        if not user_info:
            self.write_error(404)
            return

        current_user = self.current_user
        page = int(self.get_argument("p", "1"))
        template_variables["user_info"] = user_info
        template_variables["gen_random"] = gen_random
        template_variables["active_page"] = "_blank"
        self.render("topic/card.html", **template_variables)

class VoteHandler(BaseHandler):
    def get(self, template_variables = {}):
        topic_id = int(self.get_argument("topic_id"))
        topic_info = self.topic_model.get_topic_by_topic_id(topic_id)

        if not topic_info:
            self.write(lib.jsonp.print_JSON({
                "success": 0,
                "message": "topic_not_exist",
            }))
            return

        if self.current_user["uid"] == topic_info["author_id"]:
            self.write(lib.jsonp.print_JSON({
                "success": 0,
                "message": "can_not_vote_your_topic",
            }))
            return

        if self.vote_model.get_vote_by_topic_id_and_trigger_user_id(topic_id, self.current_user["uid"]):
            self.write(lib.jsonp.print_JSON({
                "success": 0,
                "message": "already_voted",
            }))
            return

        self.vote_model.add_new_vote({
            "trigger_user_id": self.current_user["uid"],
            "involved_type": 0, # 0: topic, 1: reply
            "involved_user_id": topic_info["author_id"],
            "involved_topic_id": topic_id,
            "status": 0,
            "occurrence_time": time.strftime('%Y-%m-%d %H:%M:%S'),
        })

        self.write(lib.jsonp.print_JSON({
            "success": 1,
            "message": "thanks_for_your_vote",
        }))

        # update reputation of topic author
        topic_time_diff = datetime.datetime.now() - topic_info["created"]
        reputation = topic_info["author_reputation"] or 0
        reputation = reputation + 2 * math.log(self.current_user["reputation"] or 0 + topic_time_diff.days + 10, 10)
        self.user_model.set_user_base_info_by_uid(topic_info["author_id"], {"reputation": reputation})

class UserTopicsHandler(BaseHandler):
    def get(self, user, template_variables = {}):
        if(re.match(r'^\d+$', user)):
            user_info = self.user_model.get_user_by_uid(user)
        else:
            user_info = self.user_model.get_user_by_username(user)

        current_user = self.current_user
        page = int(self.get_argument("p", "1"))
        template_variables["user_info"] = user_info
        if(user_info):
            template_variables["user_info"]["counter"] = {
                "topics": self.topic_model.get_user_all_topics_count(user_info["uid"]),
                "replies": self.reply_model.get_user_all_replies_count(user_info["uid"]),
                "favorites": self.favorite_model.get_user_favorite_count(user_info["uid"]),
            }

        if(current_user):
            template_variables["notifications_count"] = self.notification_model.get_user_unread_notification_count(current_user["uid"]);

        template_variables["topics"] = self.topic_model.get_user_all_topics(user_info["uid"], current_page = page)
        template_variables["active_page"] = "topic"
        template_variables["gen_random"] = gen_random
        self.render("topic/user_topics.html", **template_variables)

class UserRepliesHandler(BaseHandler):
    def get(self, user, template_variables = {}):
        if(re.match(r'^\d+$', user)):
            user_info = self.user_model.get_user_by_uid(user)
        else:
            user_info = self.user_model.get_user_by_username(user)

        current_user = self.current_user
        page = int(self.get_argument("p", "1"))
        template_variables["user_info"] = user_info
        if(user_info):
            template_variables["user_info"]["counter"] = {
                "topics": self.topic_model.get_user_all_topics_count(user_info["uid"]),
                "replies": self.reply_model.get_user_all_replies_count(user_info["uid"]),
                "favorites": self.favorite_model.get_user_favorite_count(user_info["uid"]),
            }

        if(current_user):
            template_variables["notifications_count"] = self.notification_model.get_user_unread_notification_count(current_user["uid"]);

        template_variables["replies"] = self.reply_model.get_user_all_replies(user_info["uid"], current_page = page)
        template_variables["active_page"] = "topic"
        template_variables["gen_random"] = gen_random
        self.render("topic/user_replies.html", **template_variables)

class UserFavoritesHandler(BaseHandler):
    def get(self, user, template_variables = {}):
        if(re.match(r'^\d+$', user)):
            user_info = self.user_model.get_user_by_uid(user)
        else:
            user_info = self.user_model.get_user_by_username(user)

        current_user = self.current_user
        page = int(self.get_argument("p", "1"))
        template_variables["user_info"] = user_info
        if(user_info):
            template_variables["user_info"]["counter"] = {
                "topics": self.topic_model.get_user_all_topics_count(user_info["uid"]),
                "replies": self.reply_model.get_user_all_replies_count(user_info["uid"]),
                "favorites": self.favorite_model.get_user_favorite_count(user_info["uid"]),
            }

        if(current_user):
            template_variables["notifications_count"] = self.notification_model.get_user_unread_notification_count(current_user["uid"]);

        template_variables["favorites"] = self.favorite_model.get_user_all_favorites(user_info["uid"], current_page = page)
        template_variables["active_page"] = "topic"
        template_variables["gen_random"] = gen_random
        self.render("topic/user_favorites.html", **template_variables)

class ReplyEditHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, reply_id, template_variables = {}):
        user_info = self.current_user
        template_variables["user_info"] = user_info
        template_variables["user_info"]["counter"] = {
            "topics": self.topic_model.get_user_all_topics_count(user_info["uid"]),
            "replies": self.reply_model.get_user_all_replies_count(user_info["uid"]),
            "favorites": self.favorite_model.get_user_favorite_count(user_info["uid"]),
        }

        template_variables["notifications_count"] = self.notification_model.get_user_unread_notification_count(user_info["uid"]);
        template_variables["reply"] = self.reply_model.get_reply_by_reply_id(reply_id)
        template_variables["gen_random"] = gen_random
        template_variables["active_page"] = "topic"
        self.render("topic/reply_edit.html", **template_variables)

    @tornado.web.authenticated
    def post(self, reply_id, template_variables = {}):
        template_variables = {}

        # validate the fields

        form = ReplyEditForm(self)

        if not form.validate():
            self.get(reply_id, {"errors": form.errors})
            return

        # continue while validate succeed

        reply_info = self.reply_model.get_reply_by_reply_id(reply_id)

        if(not reply_info["author_id"] == self.current_user["uid"]):
            template_variables["errors"] = {}
            template_variables["errors"]["invalid_permission"] = [u"没有权限修改该回复"]
            self.get(reply_id, template_variables)
            return

        update_reply_info = {
            # "content": XssCleaner().strip(form.content.data),
            "content": form.content.data,
            "updated": time.strftime('%Y-%m-%d %H:%M:%S'),
        }

        reply_id = self.reply_model.update_reply_by_reply_id(reply_id, update_reply_info)

        # update reputation of topic author
        reputation = self.current_user["reputation"] or 0
        reputation = reputation - 2
        reputation = 0 if reputation < 0 else reputation
        self.user_model.set_user_base_info_by_uid(reply_info["author_id"], {"reputation": reputation})
        self.redirect("/t/%s" % reply_info["topic_id"])

class FavoriteHandler(BaseHandler):
    def get(self, template_variables = {}):
        topic_id = int(self.get_argument("topic_id"))
        topic_info = self.topic_model.get_topic_by_topic_id(topic_id)

        if not self.current_user:
            self.write(lib.jsonp.print_JSON({
                "success": 0,
                "message": "user_not_login",
            }))
            return

        if not topic_info:
            self.write(lib.jsonp.print_JSON({
                "success": 0,
                "message": "topic_not_exist",
            }))
            return

        if self.current_user["uid"] == topic_info["author_id"]:
            self.write(lib.jsonp.print_JSON({
                "success": 0,
                "message": "can_not_favorite_your_topic",
            }))
            return

        if self.favorite_model.get_favorite_by_topic_id_and_owner_user_id(topic_id, self.current_user["uid"]):
            self.write(lib.jsonp.print_JSON({
                "success": 0,
                "message": "already_favorited",
            }))
            return

        self.favorite_model.add_new_favorite({
            "owner_user_id": self.current_user["uid"],
            "involved_type": 0, # 0: topic, 1: reply
            "involved_topic_id": topic_id,
            "created": time.strftime('%Y-%m-%d %H:%M:%S'),
        })

        self.write(lib.jsonp.print_JSON({
            "success": 1,
            "message": "favorite_success",
        }))

        # update reputation of topic author
        topic_time_diff = datetime.datetime.now() - topic_info["created"]
        reputation = topic_info["author_reputation"] or 0
        reputation = reputation + 2 * math.log(self.current_user["reputation"] or 0 + topic_time_diff.days + 10, 10)
        self.user_model.set_user_base_info_by_uid(topic_info["author_id"], {"reputation": reputation})

class CancelFavoriteHandler(BaseHandler):
    def get(self, template_variables = {}):
        topic_id = int(self.get_argument("topic_id"))
        topic_info = self.topic_model.get_topic_by_topic_id(topic_id)
        favorite_info = None

        if not self.current_user:
            self.write(lib.jsonp.print_JSON({
                "success": 0,
                "message": "user_not_login",
            }))
            return

        if not topic_info:
            self.write(lib.jsonp.print_JSON({
                "success": 0,
                "message": "topic_not_exist",
            }))
            return

        favorite_info = self.favorite_model.get_favorite_by_topic_id_and_owner_user_id(topic_id, self.current_user["uid"])

        if not favorite_info:
            self.write(lib.jsonp.print_JSON({
                "success": 0,
                "message": "not_been_favorited",
            }))
            return

        self.favorite_model.cancel_exist_favorite_by_id(favorite_info["id"])

        self.write(lib.jsonp.print_JSON({
            "success": 1,
            "message": "cancel_favorite_success",
        }))

        # update reputation of topic author
        topic_time_diff = datetime.datetime.now() - topic_info["created"]
        reputation = topic_info["author_reputation"] or 0
        reputation = reputation + 2 * math.log(self.current_user["reputation"] or 0 + topic_time_diff.days + 10, 10)
        self.user_model.set_user_base_info_by_uid(topic_info["author_id"], {"reputation": reputation})


class BlockTopicHandler(BaseHandler):
    def get(self, template_variables = {}):
        topic_id = int(self.get_argument("topic_id"))
        topic_info = self.topic_model.get_topic_by_topic_id(topic_id)

        if not self.current_user:
            self.write(lib.jsonp.print_JSON({
                "success": 0,
                "message": "user_not_login",
            }))
            return

        if not topic_info:
            self.write(lib.jsonp.print_JSON({
                "success": 0,
                "message": "topic_not_exist",
            }))
            return

        if self.current_user["uid"] == topic_info["author_id"]:
            self.write(lib.jsonp.print_JSON({
                "success": 0,
                "message": "can_not_block_your_topic",
            }))
            return

        if self.blocked_model.get_user_blocked_topic_by_involved_topic_id_and_trigger_user_id(topic_id, self.current_user["uid"]):
            self.write(lib.jsonp.print_JSON({
                "success": 0,
                "message": "already_blocked",
            }))
            return

        self.blocked_model.add_new_blocked({
            "trigger_user_id": self.current_user["uid"],
            "involved_topic_id": topic_id,
            "status": 0,#0: blocked by user; 1: blocked by admin
            "created": time.strftime('%Y-%m-%d %H:%M:%S'),
        })

        self.write(lib.jsonp.print_JSON({
            "success": 1,
            "message": "block_success",
        }))

        # update reputation of topic author
        '''topic_time_diff = datetime.datetime.now() - topic_info["created"]
        reputation = topic_info["author_reputation"] or 0
        reputation = reputation + 2 * math.log(self.current_user["reputation"] or 0 + topic_time_diff.days + 10, 10)
        self.user_model.set_user_base_info_by_uid(topic_info["author_id"], {"reputation": reputation})'''

class MembersHandler(BaseHandler):
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

        template_variables["members"] = self.user_model.get_users_by_latest(num = 49)
        template_variables["active_members"] = self.user_model.get_users_by_last_login(num = 49)
        template_variables["gen_random"] = gen_random
        template_variables["active_page"] = "members"
        self.render("topic/members.html", **template_variables)


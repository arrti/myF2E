#!/usr/bin/env python
# coding=utf-8
#
# Copyright 2012 F2E.im
# Do have a faith in what you're doing.
# Make your life a story worth telling.

from wtforms import TextField, validators
from lib.forms import Form

class SettingAlbumForm(Form):
    description = TextField('Description', [
        validators.Optional(),
        validators.Length(min = 2, message = "照片描述过短（2-50个字符）"),
        validators.Length(max = 50, message = "照片描述过长（2-50个字符）"),
    ])

class UpdateDescriptionForm(Form):
    description = TextField('Description', [
        validators.Optional(),
        validators.Length(min = 2, message = "照片描述过短（2-50个字符）"),
        validators.Length(max = 50, message = "照片描述过长（2-50个字符）"),
    ])

    imgid = TextField('Imgid', [
        validators.Required(message = "要添加描述的照片不明确"),
    ])
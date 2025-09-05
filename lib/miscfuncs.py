#
# Copyright (c) 2025 Sensia Global
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

# Python client interface for HCC2 SDK 2.0
#
import logging
import re
from dateutil import tz
import pytz

def validateUrl(url):
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:A-Z0-9?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'[A-Z0-9-_]+|'  # single name with underscores and dashes
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )
    return re.match(regex, url) is not None

def convert_datetime_to_unix_time(dt):
    return int(dt.timestamp() * 1000)

def text_to_log_level (str):
    if str=="INFO":
        return logging.INFO
    if str=="DEBUG":
        return logging.DEBUG
    if str=="WARN":
        return logging.WARN
    if str=="ERROR":
        return logging.ERROR
    return logging.DEBUG


def convert_datetime_to_UTC(dt):
    return dt.astimezone(pytz.UTC)

def convert_UTC_to_datetime(dt):
    return dt.astimezone(tz.local())


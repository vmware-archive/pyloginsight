#!/usr/bin/env python

# VMware vRealize Log Insight SDK
# Copyright (c) 2015 VMware, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


class Username(object):
    """ Represents a username parameter. """
    def __init__(self):
        self.value = None

    def __get__(self, instance, owner):
        return self.value

    def __set__(self, insance, value):
        self.value = str(value)


class Password(object):
    """ Represents a password parameter. """
    def __init__(self):
        self.value = None

    def __get__(self, instance, owner):
        return self.value

    def __set__(self, insance, value):
        self.value = str(value)


class Provider(object):
    """ Represents a provider parameter. """
    def __init__(self):
        self.value = None

    def __get__(self, instance, owner):
        return self.value 

    def __set__(self, insance, value):
        self.value = str(value)


class SessionId(object):
    """ Represents a SessionId response. """
    def __init__(self):
        self.value = None

    def __get__(self, instance, owner):
        if self.value:
            return self.value
        elif not self.value and instance.validate():
            raise NotImplementedError
        else:
            raise

    def __set__(self, insance, value):
        raise NotImplementedError


class UserId(object):
    """ Represents a UserId response. """
    def __init__(self):
        self.value = None

    def __get__(self, instance, owner):
        if self.value:
            return self.value
        elif not self.value and instance.validate():
            raise NotImplementedError

    def __set__(self, insance, value):
        raise NotImplementedError


class Alive(object):
    """ Returns whether or not the session is alive. """
    def __init__(self):
        self.value = None

    def __get__(self, instance, owner):
        pass

    def __set__(self, instance, value):
        self.value = value


class Session(object):
    def __init__(self):
        self.username = Username()
        self.password = Password()
        self.provider = Provider()
        self.sessionid = SessionId()
        self.userid = UserId()
        self.alive = Alive()

    def validate(self):
        if self.username and self.password and self.provider:
            return True
        else:
            return False

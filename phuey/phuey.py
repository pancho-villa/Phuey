#!/usr/bin/env python3
from sys import stdout
import argparse
import hashlib
import http.client
import json
import logging
import socket
import time
import urllib.error
import urllib.parse
import urllib.request

logger = logging.getLogger(__name__)

error_codes = {1:  "Unauthorized User",
              2:   "Invalid JSON",
              3:   "Resource not available",
              4:   "Method not available for resource",
              5:   "Missing parameters in body",
              6:   "Parameter not available",
              7:   "Invalid value for parameter",
              8:   "Parameter not available",
              9:   "Parameter is modifiable",
              11:  "Too many items in list",
              12:  "Portal connection required",
              901: "Internal error"}

class HueObject:
    def __init__(self, ip, username):
        self.ip = ip
        self.create_user_url = "http://" + ip + "/api"
        self.base_uri = self.create_user_url + "/" + username
        self.user = username
        self.logger = logging.getLogger(__name__ + ".HueObject")
        self.device_type = 'phuey'

    def _req(self, url, payload=None, meth="GET"):
        self.logger.debug("{} on {}".format(meth, url, payload))
        body = json.dumps(payload).encode()
        if payload:
            self.logger.debug("Body: {}".format(payload))
            request = urllib.request.Request(url, body, method=meth)
        else:
            request = urllib.request.Request(url, method=meth)
        try:
            response = urllib.request.urlopen(request)
        except urllib.error.URLError as ue:
            self.logger.critical("Couldn't connect to bridge reason: {}".format(
                                                                    ue.reason))
            self.logger.error(ue.code)
            exit()
        except ConnectionRefusedError:
            self.logger.critical("Connection refused from bridge!")
            exit()
        else:
            self.logger.debug("Bridge header response: %s" %
                              response.getheaders())
            self.logger.debug("status: {}".format(response.status))
            resp_payload = response.read().decode("utf-8")
            self.logger.debug("Bridge response: %s" % resp_payload)
            payload = self.error_check_response(resp_payload)
            return payload

    def error_check_response(self, non_json_payload):
        payload = json.loads(non_json_payload)
        if isinstance(payload, list) and 'error' in payload[0]:
            description = payload[0]['error']['description']
            self.logger.error(description)
            if isinstance(self, Light) and 'off' not in description:
                self.logger.warning("Is this a Link or Lux bulb?")
                self.logger.error("Can't change this parameter!")
        else:
            return payload

    def authorize(self):
        auth_payload = {'devicetype': self.device_type, 'username': self.user}
        self.logger.debug(auth_payload)
        self._req(self.create_user_url, auth_payload, "POST")

    def __str__(self):
        if isinstance(self, Light):
            return "Light id: {} name: {} currently on: {}".format(
                               self.light_id, str(self.name), self.on)
        elif isinstance(self, Bridge):
            self.logger.debug(type(self))
            return "name: {} with {} light(s)".format(self.name,
                                                      len(self.lights))
        elif isinstance(self, Scene):
            self.logger.debug(type(self))
            return "Scenes: {}".format(self.scenes)
        elif isinstance(self, Group):
            return "Group: {}".format(self.name)

    def __repr__(self):
        if isinstance(self, Light):
            return "Light id: {} name: {} currently on: {}".format(
                               self.light_id, str(self.name), self.on)
        else:
            return 'Bazinga!'


class HueDescriptor:
    def __init__(self, name, initval):
        self.name = initval
        self.__name__ = name
        self.logger = logging.getLogger(__name__ + ".HueDescriptor")

    def __get__(self, inst, cls):
        self.logger.debug("calling get on {}".format(type(inst)))
        self.logger.debug("{} keys".format(inst.__dict__.keys()))
        return inst.__dict__[self.__name__]

    def __set__(self, inst, val):
        dbg_msg = "calling set on: {} from: {} to: {} ".format(self.__name__,
                                                               self.name, val)
        self.logger.debug(dbg_msg)
        if val is None:
            val = "none"
        if self.__name__ is 'state':
            self.logger.debug("__name__ is state!")
            for key, value in val.items():
                logger.debug('{} {}'.format(inst.__dict__.keys(), key))
                inst.__dict__[key] = value
            inst._req(inst.state_uri, val, "PUT")
            return
        if self.__name__ is not 'light_id':
            self.logger.debug("val: {}".format(val))
            if isinstance(inst, Light) and self.__name__ == "name":
                self.logger.debug("{} {}".format(val, type(val)))
                self.logger.debug(inst.__dict__.keys())
                self.logger.debug(type(inst))
                if (inst.__dict__[self.__name__] is not None or
                inst.__dict__[self.__name__] is not "None"):
                    self.logger.debug("self.__name__ is {}".format(
                                                               self.__name__))
                    input('press enter to continue...')
            elif isinstance(inst, Light) and self.__name__ != "name":
                if val is not None:
                    self.logger.debug("calling req against: {}".format(
                                                              inst.state_uri))
                    inst._req(inst.state_uri, {self.__name__: val}, "PUT")

            else:
                self.logger.debug("How the fuck did I get here?")
                self.logger.debug("type of {} is {}".format(inst, type(inst)))
                self.logger.debug(self.__name__)
                quit(0)

        else:
            self.logger.debug("{} {} {}".format(self.__name__, self.name, val))
            self.logger.debug("{} is None!".format(self.__name__))
        inst.__dict__[self.__name__] = val
        self.logger.debug(inst.__dict__.keys())

    def __str__(self):
        return self.name


class Light(HueObject):
    on = HueDescriptor('on', None)
    bri = HueDescriptor('bri', None)
    xy = HueDescriptor('xy', None)
    ct = HueDescriptor('ct', None)
    sat = HueDescriptor('sat', None)
    hue = HueDescriptor('hue', None)
    alert = HueDescriptor('alert', None)
    effect = HueDescriptor('effect', None)
    state = HueDescriptor('state', None)
    transitiontime = HueDescriptor('transitiontime', None)

    def __init__(self, ip, username, light_id, name, start_state=None):
        super().__init__(ip, username)
        self.light_id = light_id
        self.name = HueDescriptor('name', name)
        self.logger = logging.getLogger(__name__ + ".Light")
        self.name_uri = self.base_uri + "/lights/" + str(self.light_id)
        self.state_uri = self.name_uri + "/state"
        if start_state:
            self.logger.debug(type(start_state))
            self.logger.debug(start_state)
            for key, value in json.loads(start_state).items():
                self.logger.debug("Setting {} with {}".format(key, value))
                self.__dict__[key] = value
        self.__dict__['transitiontime'] = 4

    def __gt__(self, other):
        return self.light_id > other.light_id

    def __lt__(self, other):
        return self.light_id < other.light_id

    def __eq__(self, other):
        return not self.light_id < other and not other.light_id < self.light_id


class Group(HueObject):
    scene = HueDescriptor('scene', None)
    def __init__(self, ip, user, name, light_list, allow_dupes=False):
        super().__init__(ip, user)
        self.logger = logging.getLogger(__name__ + ".Group")
        self.name = name
        self.lights = self.validate_light_list(light_list)
        self.create_uri = self.base_uri + "/groups"
        payload = {"lights": self.lights, "name": name}
        cached = self._req(self.create_uri)
        found = False
        for k, v in cached.items():
            if name == v["name"]:
                if not allow_dupes:
                    same = "Found group {} with the same name".format(k)
                    self.logger.warning(same)
                    self.logger.info("Group not created")
                    self.get_id_uri(None, int(k))
                    found = True
                    break
                else:
                    self._req(self.uri, payload, "POST")
        if not found:
            bridge_response = self._req(self.create_uri, payload, "POST")
            try:
                self.get_id_uri(bridge_response)
            except KeyError as ke:
                self.logger.error(ke)                
 
    def get_id_uri(self, bridge_response=None, group_id=None):
        if bridge_response:
            resp = bridge_response[0]['success']['id']
            self.logger.debug(resp)
            self.id = int(resp.split("/")[2])
        if group_id:
            self.id = group_id
        self.uri = self.create_uri + "/" + str(self.id)


    def validate_light_list(self, light_list):
        for i, item in enumerate(light_list):
            self.logger.debug(item)
            if type(item) is not str and type(item) is int:
                light_list[i] = str(item)
                self.logger.debug("Mutating {}".format(item))
            else:
                self.logger.error("Wrong type in the light list")
        self.logger.debug(light_list)
        return light_list

    def remove(self):
        response = self._req(self.uri, None, "DELETE")
        try:
            message = response[0]['success']
        except KeyError as ke:
            self.logger.error(ke)
        except TypeError as te:
            self.logger.error(te)
            self.logger.error("Received empty response from server")
        else:
            self.logger.info("Group name {} id {} deleted".format(self.name,
                                                                  self.id))


class Scene(HueObject):
    def __init__(self, ip, user):
        super().__init__(ip, user)
        self.logger = logging.getLogger(__name__ + ".Scene")
        self.create_uri = self.base_uri + "/scenes"
        self.scenes = self._req(self.create_uri)

            
class Bridge(HueObject):
    def __init__(self, ip, user):
        super().__init__(ip, user)
        self.logger = logging.getLogger(__name__ + ".Bridge")
        try:
            lights_dict = self._req(self.base_uri)
        except KeyError as ke:
            self.logger.error(ke)
            lights_dict = self._req(self.base_uri)
        self.logger.debug(lights_dict)
        self.name = lights_dict['config']['name']
        self.lights = []
        self.logger.debug(self.__dict__)
        for key, value in lights_dict['lights'].items():
            self.logger.debug("Key: {} Value: {}".format(key, value['state']))
            if str(key).isdigit():
                state = json.dumps(value['state'])
                name = value['name']
                light = Light(ip, user, int(key), name, state)
                self.logger.debug("Created this light: {}".format(light))
                self.__dict__[key] = light
                self.lights.append(light)
            else:
                self.logger.debug("Whawt?!")
                self.logger.debug(str(key).isdigit())
        self.logger.debug("all lights in bridge: {}".format(self.__dict__))

    def __len__(self):
        return len(self.lights)

    def __getitem__(self, key):
        if isinstance(key, str):
            self.logger.debug("returning by key: {}".format(key))
            for value in self.__dict__.values():
                if isinstance(value, Light):
                    self.logger.debug(value)
                    name = str(value.name)
                    if name.lower() == key.lower():
                        return value
                else:
                    self.logger.debug("{} != {}".format(value, key))
            return "Can't find light by id or name of {}".format(key)
        else:
            self.logger.debug('returning by light id')
            return self._get_light_by_id(key)

    def __setitem__(self, key, value):
        self.logger.debug("calling setitem with {}:{}".format(key, value))
        self.logger.debug("setting item with {}".format(type(value)))
        if (isinstance(key, str) or isinstance(key, int)) and isinstance(value,
                                                                        int):
            self.logger.debug('key is string and value is int!')
            self.lights[key] = value
        elif (isinstance(key, str) or isinstance(key, int) and
              isinstance(value, dict)):
            if key.lower != "state":
                raise ValueError("Can't set any attribute but state with a dictionary")
            self.logger.debug("what? it should go off here!")
            self.logger.debug(value)
            self.logger.debug(key)
            self.lights[key] = value
        else:
            self._get_light_by_id(key)

    def _get_light_by_id(self, lid):
        light_id = str(lid)
        self.logger.debug("trying to match against %s" % light_id)
        return self.__dict__.get(light_id)


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--bridge', '-b', metavar="BRIDGEIPADDRESS")
    arg_parser.add_argument('--user', '-u', metavar="USERNAME")
    args = arg_parser.parse_args()
    bridge_ip = args.bridge
    user = args.user
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler(stdout)
    ch.setLevel(logging.DEBUG)
    fmt = '%(name)s - %(asctime)s - %(module)s-%(funcName)s/%(lineno)d - %(message)s'
    formatter = logging.Formatter(fmt)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    bridge_ip = '192.168.1.116'
    user = '23c05db12a8212d7c359e528b19f0b'
    b = Bridge(bridge_ip, user)

    for light in sorted(b.lights):
        print(light)

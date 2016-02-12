#!/usr/bin/env python3
import argparse
import json
import logging
import sys

__version__ = "1.0.1"
__updated__ = "2016-02-12"
logger = logging.getLogger('phuey')

major, minor = sys.version_info[0:2]
if (major, minor) == (2, 6) or (major, minor) == (2, 7):
    try:
        import httplib as http_client
    except ImportError as ie:
        logger.error(ie)
        msg = "Error httplib not found in this version: {}.{}"
        logger.critical(msg.format(major, minor))
        raise ImportError
elif major == 2 and minor < 6:
    raise RuntimeError("Not supported on Python versions older than 2.6")
elif major >= 3:
    import http.client as http_client


def get_version():
    return __version__


def get_args():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--bridge', '-b', metavar="BRIDGEIPADDRESS")
    arg_parser.add_argument('--user', '-u', metavar="USERNAME")
    arg_parser.add_argument('--verbose', '-v', action="store_true",
                            default=False)
    args = arg_parser.parse_args()
    bridge_ip = args.bridge
    user = args.user
    if args.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    return bridge_ip, user, log_level


class HueObject:
    def __init__(self, ip, username):
        self.ip = ip
        self.create_user_url = "/api"
        self.base_uri = self.create_user_url + "/" + username
        self.user = username
        self.logger = logging.getLogger(__name__ + ".HueObject")
        self.device_type = 'phuey'

    def _req(self, url, payload=None, meth="GET"):
        self.logger.debug("HTTP {} on {}".format(meth, url, payload))
        connection = http_client.HTTPConnection(self.ip, 80, timeout=3)
        body = None
        if payload:
            body = json.dumps(payload).encode()
            self.logger.debug("Body: {}".format(payload))
        ct = {"Content-type": "application/json"}
        connection.request(meth, url, body, ct)
        try:
            response = connection.getresponse()
        except ConnectionRefusedError:
            self.logger.critical("Connection refused from bridge!")
            exit()
        else:
            if response.status >= 400:
                self.logger.error(response.reason)
                raise ValueError("Invalid server response")
            self.logger.debug("Bridge header response: {}".format(
                                                      response.getheaders()))
            self.logger.debug("status: {}".format(response.status))
            resp_payload = response.read().decode("utf-8")
            self.logger.debug("Bridge response: {}".format(resp_payload))
            payload = self.error_check_response(resp_payload)
            return payload

    def find_new_lights(self):
        add_light_url = self.base_uri + "/lights"
        resp = self._req(add_light_url, None, "POST")
        result_code, message = list(resp[0].keys()), list(resp[0].values())
        if result_code == 'success':
            logger.info(message[0]['/lights'])
        else:
            logger.error(message[0])

    def error_check_response(self, non_json_payload):
        payload = json.loads(non_json_payload)
        if isinstance(payload, list) and 'error' in payload[0]:
            description = payload[0]['error']['description']
            self.logger.error(description)
            self.logger.error(payload)
            if isinstance(self, ZigbeeLight):
                self.logger.warning("Is this a Link or Lux bulb?")
                raise AttributeError(description)
        else:
            return payload

    def authorize(self):
        auth_payload = {'devicetype': self.device_type, 'username': self.user}
        self.logger.debug(auth_payload)
        self._req(self.create_user_url, auth_payload, "POST")

    def __str__(self):
        if isinstance(self, ZigbeeLight):
            return "Light id: {} name: {}".format(
                               self.light_id, str(self.name))
        elif isinstance(self, Bridge):
            self.logger.debug(type(self))
            return "name: {} with {} light(s)".format(self.name,
                                                      len(self.lights))
        elif isinstance(self, Scene):
            return "Scenes: {}".format(self.all)
        elif isinstance(self, Group):
            groups = []
            for key, _ in self.__dict__.items():
                if key.isdigit():
                    groups.append(key)

            return "Group IDs: {}".format(sorted(groups))

    def __repr__(self):
        if isinstance(self, ZigbeeLight):
            return "Light id: {} name: {} currently on: {}".format(
                               self.light_id, str(self.name), self.on)
        elif isinstance(self, Scene):
            return "Scenes: {}".format(self.all)
        else:
            msg = "HueObject can't coerce the repr method for your object"
            logger.error(msg)
            return 'ERROR'


class HueDescriptor:
    def __init__(self, name, initval):
        self.logger = logging.getLogger(__name__ + ".HueDescriptor")
        self.logger.debug("{} is self.name".format(initval))
        self.logger.debug("{} is self.__name__".format(name))
        self.name = initval
        self.__name__ = name

    def __get__(self, inst, cls):
        self.logger.debug("calling get on {} of {} type".format(inst, cls))
        try:
            return inst.__dict__[self.__name__]
        except KeyError as ke:
            msg = "{} not a valid read parameter for {}".format(ke, inst)
            self.logger.error(msg)
            self.logger.debug(inst.__dict__)
            self.logger.error("POOOOOOOOOOOOOOP")
            raise KeyError

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
            if isinstance(inst, ZigbeeLight) and self.__name__ == "name":
                self.logger.debug("{} {}".format(val, type(val)))
                if (inst.__dict__[self.__name__] is not None or
                        inst.__dict__[self.__name__] is not "None"):
                    self.logger.debug("self.__name__ is {}".format(
                                                               self.__name__))
                    input('press enter to continue...')
            elif isinstance(inst, ZigbeeLight) and self.__name__ != "name":
                if val is not None:
                    self.logger.debug("calling req against: {}".format(
                                                              inst.state_uri))
                    inst._req(inst.state_uri, {self.__name__: val}, "PUT")

            elif isinstance(inst, Group):
                payload = {self.__name__: val}
                inst._req(inst.state_uri, payload, "PUT")
            else:
                self.logger.debug("How the fuck did I get here?")
                self.logger.debug("type of {} is {}".format(inst, type(inst)))
                self.logger.debug(self.__name__)
                raise RuntimeError("wtf matey!")

        else:
            self.logger.debug("{} {} {}".format(self.__name__, self.name, val))
            self.logger.debug("{} is None!".format(self.__name__))
        inst.__dict__[self.__name__] = val
        self.logger.debug(inst.__dict__.keys())

    def __str__(self):
        return self.name


class ZigbeeLight(HueObject):
    """Can be a GE Link light or Hue Lux Light"""
    on = HueDescriptor('on', None)
    bri = HueDescriptor('bri', None)
    state = HueDescriptor('state', None)
    transitiontime = HueDescriptor('transitiontime', None)
    reachable = HueDescriptor('reachable', None)
    name = HueDescriptor('name', None)

    def __init__(self, ip, username, light_id=None, name=None, model=None,
                 start_state=None):
        self.logger = logging.getLogger(__name__ + ".ZigbeeLight")
        super().__init__(ip, username)
        self.light_id = light_id
        self.modelid = model
        self.name_uri = self.base_uri + "/lights/" + str(self.light_id)
        self.get_state_uri = self.name_uri
        self.state_uri = self.name_uri + "/state"
        for key, value in json.loads(start_state).items():
            self.__dict__[key] = value

    def __gt__(self, other):
        return self.light_id > other.light_id

    def __lt__(self, other):
        return self.light_id < other.light_id

    def __eq__(self, other):
        return not self.light_id < other and not other.light_id < self.light_id

    def __getitem__(self, key):
        self.logger.debug("calling __getitem__ on {}".format(self.__inst__))
        if isinstance(key, str):
            self.logger.debug("returning by key: {}".format(key))
            for dict_key, value in self.__dict__.items():
                logger.debug(value)
                logger.debug(type(value))
                if key.lower() == dict_key.lower():
                    return value


class HueLight(ZigbeeLight):
    xy = HueDescriptor('xy', None)
    ct = HueDescriptor('ct', None)
    sat = HueDescriptor('sat', None)
    hue = HueDescriptor('hue', None)
    alert = HueDescriptor('alert', None)
    effect = HueDescriptor('effect', None)

    def __init__(self, ip, username, light_id=None, name=None, model=None,
                 start_state=None):
        self.logger = logging.getLogger(__name__ + ".HueLight")
        super().__init__(ip, username, light_id, name, model, start_state)
        self.light_id = light_id
        self.modelid = model
        self.name = HueDescriptor('name', name)
        self.name_uri = self.base_uri + "/lights/" + str(self.light_id)
        self.get_state_uri = self.name_uri
        self.state_uri = self.name_uri + "/state"
        for key, value in json.loads(start_state).items():
            self.__dict__[key] = value


class Group(HueObject):
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
    reachable = HueDescriptor('reachable', None)

    def __init__(self, ip, user, group_id):
        super().__init__(ip, user)
        self.group_id = group_id
        self.logger = logging.getLogger(__name__ + ".Group")
        self.create_uri = self.base_uri + "/groups"
        self.uri = self.create_uri + "/" + str(self.group_id)
        self.state_uri = self.uri + "/action"

    def remove(self, group_id):
        response = self._req(self.uri, None, "DELETE")
        try:
            _ = response[0]['success']
        except KeyError as ke:
            self.logger.error(ke)
        except TypeError as te:
            self.logger.error(te)
            self.logger.error("Received empty response from server")
        else:
            self.logger.info("Group id {} deleted".format(group_id))


class Scene(HueObject):
    def __init__(self, ip, user, scene_id=None):
        super().__init__(ip, user)
        self.scene_id = scene_id
        self.logger = logging.getLogger(__name__ + ".Scene")
        self.create_uri = self.base_uri + "/scenes"
        self.all = self._req(self.create_uri)
        self.__dict__ = {k: v for k, v in self.all.items()}

    def __len__(self):
        return len(self.__dict__)

    def __getitem__(self, key):
        return self.__dict__[key]


class Bridge(HueObject):
    def __init__(self, ip, user):
        super().__init__(ip, user)
        self.logger = logging.getLogger(__name__ + ".Bridge")
        lights_dict = self._req(self.base_uri)
        self.name = lights_dict['config']['name']
        self.lights = []
        self.logger.debug(self.__dict__)
        for key, value in lights_dict['lights'].items():
            self.logger.debug("Key: {} Value: {}".format(key, value['state']))
            state = json.dumps(value['state'])
            name = value['name']
            model = value['modelid']
#            create proper light class depending on light model
            if model == 'LCT001':
                light = HueLight(ip, user, int(key), name, model, state)
#            lct001 are hue color bulbs, lwb004 are hue white and zll light are
#            white ge link lights
            elif model == 'LWB004' or model == 'ZLL Light':
                light = ZigbeeLight(ip, user, int(key), name, model, state)
            self.logger.debug("Created this light: {}".format(light))
            self.__dict__[key] = light
            self.lights.append(light)

    def __len__(self):
        return len(self.lights)

    def __getitem__(self, key):
        if isinstance(key, str):
            self.logger.debug("returning by key: {}".format(key))
            for value in self.__dict__.values():
                if isinstance(value, ZigbeeLight):
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
                msg = "Can't set any attribute but state with a dictionary"
                raise ValueError(msg)
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
    bridge_ip, user, log_level = get_args()
    logger.setLevel(log_level)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(log_level)
    fmt = '%(levelname)s %(name)s - %(asctime)s - %(lineno)d - %(message)s'
    formatter = logging.Formatter(fmt)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

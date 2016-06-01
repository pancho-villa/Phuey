#!/usr/bin/env python3
import argparse
import json
import logging
import sys
from socket import timeout

__version__ = "1.0"
__updated__ = "2016-06-01"

logger = logging.getLogger()

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
        connection = http_client.HTTPConnection(self.ip, 80, timeout=5)
        body = None
        if payload:
            body = json.dumps(payload).encode()
            self.logger.debug("Body: {}".format(payload))
        ct = {"Content-type": "application/json"}
        try:
            connection.request(meth, url, body, ct)
            response = connection.getresponse()
        except ConnectionRefusedError:
            self.logger.critical("Connection refused from bridge!")
            raise ConnectionRefusedError("Ensure IP address is correct")
        except Exception as ee:
            self.logger.error(ee)
            raise RuntimeError(ee)
        else:
            self.logger.debug(response)
            self.logger.debug(type(response))
            self.logger.debug("status: {}".format(response.status))
            if response.status >= 400:
                self.logger.error(response.reason)
                raise RuntimeError(response.reason)
            self.logger.debug("Bridge header response: {}".format(
                                                      response.getheaders()))
            resp_payload = response.read().decode("utf-8")
            self.logger.debug("Bridge response: {}".format(resp_payload))
            payload = self.error_check_response(resp_payload)
            return payload

    def error_check_response(self, non_json_payload):
        payload = json.loads(non_json_payload)
        if isinstance(payload, list) and 'error' in payload[0]:
            description = payload[0]['error']['description']
            self.logger.error(description)
            self.logger.debug(payload)
            raise AttributeError(description)
        else:
            return payload

    def __str__(self):
        if isinstance(self, Light):
            return "Light id: {}".format(self.light_id)
        elif isinstance(self, Bridge):
            self.logger.debug(type(self))
            return "name: {} with {} light(s)".format(self.name,
                                                      len(self.lights))
        elif isinstance(self, Scene):
            return "Scenes: {}".format(self.all)
        elif isinstance(self, Group):
            return "Group id: {}".format(self.group_id)
        elif isinstance(self, Sensor):
            return "Sensor id: {}".format(self.sensor_id)
        elif isinstance(self, Schedule):
            return "Sensor id: {}".format(self.Schedule_id)

    def __repr__(self):
        if isinstance(self, Light):
            return "Light id: {} name: {} currently on: {}".format(
                               self.light_id, str(self.name), self.on)
        elif isinstance(self, Scene):
            return "Scenes: {}".format(self.all)
        else:
            msg = "HueObject can't coerce the repr method for your object"
            self.logger.error(msg)
            return 'ERROR'


class HueDescriptor:
    def __init__(self, name, initval):
        self.logger = logging.getLogger(__name__ + ".HueDescriptor")
        self.name = initval
        self.__name__ = name

    def __get__(self, inst, cls):
        self.logger.debug("calling get on {} of {} type".format(inst, cls))
        if isinstance(inst, Light):
            return inst._req(inst.name_uri)[self.__name__]
        return inst._req(inst.state_uri)['state'][self.__name__]

    def __set__(self, inst, val):
        dbg_msg = "calling set on: {} from: {} to: {} ".format(self.__name__,
                                                               self.name, val)
        self.logger.debug(dbg_msg)
        if val is None:
            val = "none"
        if self.__name__ is 'state':
            self.logger.debug("__name__ is state!")
            for key, value in val.items():
                inst.__dict__[key] = value
            inst._req(inst.state_uri, val, "PUT")
            return
        if self.__name__ is not 'light_id':
            if isinstance(inst, Light) and self.__name__ == "name":
                self.logger.debug("{} {}".format(val, type(val)))
                inst._req(inst.name_uri, {"name": val}, "PUT")

            elif isinstance(inst, Light) and self.__name__ != "name":
                if val is not None:
                    inst._req(inst.state_uri, {self.__name__: val}, "PUT")

            elif isinstance(inst, Group):
                if val is not None and isinstance(val, dict):
                    if len(val.keys()) > 1:
                        inst._req(inst.state_uri, val, "PUT")
                inst._req(inst.state_uri, {self.__name__: val}, "PUT")
            else:
                self.logger.debug("How the fuck did I get here?")
                self.logger.debug("type of {} is {}".format(inst, type(inst)))
                self.logger.debug(self.__name__)
                raise RuntimeError("wtf matey!")

        else:
            self.logger.debug("{} {} {}".format(self.__name__, self.name, val))
            return
        inst.__dict__[self.__name__] = val
        self.logger.debug(inst.__dict__.keys())

    def __str__(self):
        return self.name


class Light(HueObject):
    """Any light supported by the Phillips Hue hub"""
    on = HueDescriptor('on', None)
    xy = HueDescriptor('xy', None)
    ct = HueDescriptor('ct', None)
    bri = HueDescriptor('bri', None)
    sat = HueDescriptor('sat', None)
    hue = HueDescriptor('hue', None)
    state = HueDescriptor('state', None)
    alert = HueDescriptor('alert', None)
    effect = HueDescriptor('effect', None)
    transitiontime = HueDescriptor('transitiontime', None)
    name = HueDescriptor('name', None)
    modelid = HueDescriptor('modelid', None)

    def __init__(self, ip, username, light_id):
        self.logger = logging.getLogger(__name__ + ".Light")
        super().__init__(ip, username)
        self.light_id = light_id
        self.name_uri = self.base_uri + "/lights/" + str(self.light_id)
        self.state_uri = self.name_uri + "/state"

    def __gt__(self, other):
        return self.light_id > other.light_id

    def __lt__(self, other):
        return self.light_id < other.light_id

    def __eq__(self, other):
        return not self.light_id < other and not other.light_id < self.light_id


class Group(HueObject):
    on = HueDescriptor('on', None)
    xy = HueDescriptor('xy', None)
    ct = HueDescriptor('ct', None)
    bri = HueDescriptor('bri', None)
    sat = HueDescriptor('sat', None)
    hue = HueDescriptor('hue', None)
    state = HueDescriptor('state', None)
    alert = HueDescriptor('alert', None)
    effect = HueDescriptor('effect', None)
    transitiontime = HueDescriptor('transitiontime', None)

    def __init__(self, ip, user, group_id=None, attributes=None):
        super().__init__(ip, user)
        self.logger = logging.getLogger(__name__ + ".Group")
        self.create_uri = self.base_uri + "/groups"
        if group_id is not None:
            self.group_id = str(group_id)
        elif not group_id and attributes:
            group_data = self._req(self.create_uri, attributes, "POST")
            self.group_id = group_data[0]['success']['id']
        else:
            ve_msg = "Need either attributes or group id to create group"
            raise ValueError(ve_msg)
        self.logger.debug(self.__dict__)
        self.name_uri = self.create_uri + "/" + self.group_id
        self.state_uri = self.name_uri + "/action"

    def remove(self):
        if self.group_id != "0":
            response = self._req(self.name_uri, None, "DELETE")
            try:
                msg = response[0]['success']
            except KeyError as ke:
                self.logger.error(ke)
                raise KeyError
            except TypeError as te:
                self.logger.error(te)
                raise TypeError(te)
            else:
                self.logger.info("{}".format(msg))
        else:
            self.logger.error("Can't delete group 0!")


class Scene(HueObject):
    def __init__(self, ip, user, scene_id=None):
        super().__init__(ip, user)
        self.scene_id = scene_id
        self.logger = logging.getLogger(__name__ + ".Scene")
        self.create_uri = self.base_uri + "/scenes"

    def __len__(self):
        return len(self.__dict__)

    def __getitem__(self, key):
        return self.__dict__[key]


class Rule(HueObject):
    def __init__(self, ip, user, rule_id=None):
        super().__init__(ip, user)
        self.rule_id = rule_id
        self.logger = logging.getLogger(__name__ + ".Rule")
        self.create_uri = self.base_uri + "/rules"

    def __len__(self):
        return len(self.__dict__)

    def __getitem__(self, key):
        return self.__dict__[key]


class Sensor(HueObject):
    def __init__(self, ip, user, sensor_id=None):
        super().__init__(ip, user)
        self.sensor_id = sensor_id
        self.logger = logging.getLogger(__name__ + ".Sensor")
        self.create_uri = self.base_uri + "/sensors"

    def __len__(self):
        return len(self.__dict__)

    def __getitem__(self, key):
        return self.__dict__[key]


class Schedule(HueObject):
    def __init__(self, ip, user, schedule_id=None):
        super().__init__(ip, user)
        self.sensor_id = schedule_id
        self.logger = logging.getLogger(__name__ + ".Schedule")
        self.create_uri = self.base_uri + "/schedules"

    def __len__(self):
        return len(self.__dict__)

    def __getitem__(self, key):
        return self.__dict__[key]


class Bridge(HueObject):
    def __init__(self, ip, user=None):
        super().__init__(ip, user)
        self.logger = logging.getLogger(__name__ + ".Bridge")
        if user is None:
            self.user = self._authorize()
        bridge_dict = self._req(self.base_uri)
        self.name = bridge_dict['config']['name']
        self.lights = [] or self._iter_bridge_items(bridge_dict, 'lights')
        self.scenes = [] or self._iter_bridge_items(bridge_dict, 'scenes')
        self.groups = [] or self._iter_bridge_items(bridge_dict, 'groups')
        self.sensors = [] or self._iter_bridge_items(bridge_dict, 'sensors')
        self.rules = [] or self._iter_bridge_items(bridge_dict, 'rules')
        self.schedules = [] or self._iter_bridge_items(bridge_dict,
                                                       'schedules')

    def __len__(self):
        return len(self.lights)

    def _iter_bridge_items(self, bridge_dict, items):
        results = []
        for key, value in bridge_dict[items].items():
            self.logger.debug("Key: {} Value: {}".format(key, value))
            if items == 'lights':
                bridge_item = Light(self.ip, self.user, int(key))
            elif items == 'groups':
                bridge_item = Group(self.ip, self.user, int(key))
            elif items == 'scenes':
                bridge_item = Scene(self.ip, self.user)
            elif items == 'rules':
                bridge_item = Rule(self.ip, self.user, int(key))
            elif items == 'sensors':
                bridge_item = Sensor(self.ip, self.user, int(key))
            elif items == 'schedules':
                bridge_item = Scene(self.ip, self.user)
            self.logger.debug("Created: {}".format(bridge_item))
            results.append(bridge_item)
        return results

#     def find_new_lights(self, dev_id=None):
#         add_light_url = self.base_uri + "/lights"
#         if isinstance(dev_id, list):
#             dev_id_list = str([i for i in dev_id])
#             body = {"deviceid": dev_id_list}
#             resp = self._req(add_light_url, body, "POST")
#         elif isinstance(dev_id, str):
#             body = {"deviceid": dev_id_list}
#             resp = self._req(add_light_url, body, "POST")
#         elif dev_id is None:
#             resp = self._req(add_light_url, None, "POST")
#         result_code, message = list(resp[0].keys()), list(resp[0].values())
#         if result_code == 'success':
#             self.logger.info(message[0]['/lights'])
#         else:
#             self.logger.error(message[0])

    def _authorize(self):
        auth_payload = {'devicetype': self.device_type}
        token = self._req(self.create_user_url, auth_payload, "POST")[0]
        self.user = token['success']['username']

if __name__ == "__main__":
    bridge_ip, user, log_level = get_args()
    logger.setLevel(log_level)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(log_level)
    fmt = '%(levelname)s %(name)s - %(asctime)s - %(lineno)d - %(message)s'
    formatter = logging.Formatter(fmt)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

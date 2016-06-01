'''
Created on Jan 31, 2016

@author: pancho-villa
'''
import unittest
import logging
import sys
import phuey
# import json

from unittest.mock import patch

__updated__ = "2016-06-01"

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
fmt = '%(levelname)s %(name)s - %(asctime)s - %(lineno)d - %(message)s'
formatter = logging.Formatter(fmt)
ch.setFormatter(formatter)
logger.addHandler(ch)


class PhueyTest(unittest.TestCase):

    def setUp(self):
        self.ip = 'ip'
        self.user = 'user'
        self.patcher = patch('phuey.http_client.HTTPConnection', autospec=True)
        inst = self.patcher.start()
        self.mock = inst.return_value.getresponse
        with open('full_bridge_response.json') as fbr:
            self.full_bridge_response = bytes(fbr.read(), 'utf-8')

    def tearDown(self):
        self.patcher.stop()

    def test_use_existing_group_without_id_in_use(self):
        """initialize a group using an id not in use"""
        mock_bridge_resp = bytes('[{"error":{"description": 1}}]', 'utf-8')
        self.mock.return_value.status = 200
        self.mock.return_value.read.return_value = mock_bridge_resp
        g = phuey.Group(self.ip, self.user, 15)
        with self.assertRaises(AttributeError) as ae:
            g.on = False
        logging.debug(ae.exception)
        self.mock.assert_any_call()

    def test_use_existing_group_with_id_in_use(self):
        """initialize a group using an id not in use"""
        mock_bridge_resp = '[{"success":{"/groups/1/action/on":true}}]'
        self.mock.return_value.status = 200
        self.mock.return_value.read.return_value = bytes(mock_bridge_resp,
                                                         'utf-8')
        g = phuey.Group(self.ip, self.user, 1)
        g.on = True
        self.mock.assert_any_call()

    def test_create_bridge(self):
        """Create a new bridge, ensure no errors raised"""
        self.mock.return_value.status = 200
        self.mock.return_value.read.return_value = self.full_bridge_response
        phuey.Bridge(self.ip, self.user)
        self.mock.assert_any_call()

    def test_create_bridge_with_missing_parameters(self):
        """Create a new bridge that fails without the proper attributes"""
        mock_bridge_resp = '[{"error": {"description": 1}}]'
        self.mock.return_value.status = 200
        self.mock.return_value.read.return_value = bytes(mock_bridge_resp,
                                                         'utf-8')
        with self.assertRaises(AttributeError) as ae:
            phuey.Bridge(self.ip, 'baduser')
        logging.debug(ae.exception)
        self.mock.assert_any_call()

    def test_create_bridge_with_bad_ip(self):
        """Create a new bridge that fails without the proper address"""
        self.mock.side_effect = ConnectionRefusedError
        with self.assertRaises(ConnectionRefusedError) as ae:
            phuey.Bridge('existing_ip_on_subnet_but_not_bridge_ip', self.user)
        self.mock.assert_any_call()

    def test_create_group_with_missing_parameters(self):
        """Create a new group that fails without the proper attributes"""
        with self.assertRaises(ValueError):
            phuey.Group(self.ip, self.user, attributes={})

    def test_create_group_with_correct_parameters(self):
        attrs = {"lights": ["1", "2"]}
        self.mock.return_value.status = 200
        self.mock.return_value.read.side_effect = [bytes('[{"success":{"id":"16"}}]', 'utf-8'),
                                                   bytes('{"name":"Group 2","lights":["1","2"],"type":"LightGroup","action": {"on":true,"bri":254,"hue":14839,"sat":148,"effect":"none","xy":[0.4622,0.4111],"ct":372,"alert":"none","colormode":"ct"}}','utf-8')]
        phuey.Group(self.ip, self.user, attributes=attrs)
        self.mock.assert_any_call()

    def test_create_group_with_incorrect_parameters(self):
        attrs = {"not_lights": ["1", "2"]}
        self.mock.return_value.status = 200
        self.mock.return_value.read.return_value = bytes('[{"error":{"type":6,"address":"/groups/fuckthis","description":"parameter, fuckthis, not available"}}]', 'utf-8')
        with self.assertRaises(AttributeError):
            phuey.Group(self.ip, self.user, attributes=attrs)

        self.mock.assert_any_call()

    def test_bad_request(self):
        self.mock.return_value.status = 666
        self.mock.return_value.read = None
        with self.assertRaises(RuntimeError):
            phuey.Bridge(self.ip, self.user)

    def test_reach_lights_in_bridge(self):
        self.mock.return_value.status = 200
        self.mock.return_value.read.return_value = self.full_bridge_response
        b = phuey.Bridge(self.ip, self.user)
        for light in b.lights:
            self.assertTrue(isinstance(light, phuey.Light))
        self.mock.assert_any_call()

#     def test_create_bridge_bad_user(self):
#         self.mock.return_value.status = 200
#         self.mock.return_value.read.return_value = bytes('[{"error":{"description":1}}]', 'utf-8')
#         with self.assertRaises(AttributeError):
#             phuey.Bridge(self.ip)
#         self.mock.assert_any_call()

    def test_change_light_name(self):
        self.mock.return_value.status = 200
        self.mock.return_value.read.return_value = bytes('[{"success":{"/lights/1/name":"Bedroom Light"}}]', 'utf-8')
        l = phuey.Light(self.ip, self.user, 17)
        l.name = "Bedroom Light"
        self.mock.assert_any_call()

    def test_change_light_state(self):
        self.mock.return_value.status = 200
        self.mock.return_value.read.return_value = bytes('[{"success": {"/lights/17/state/sat": 254}}]', 'utf-8')
        l = phuey.Light(self.ip, self.user, 17)
        l.state = {"sat": 254}
        self.mock.assert_any_call()

if __name__ == "__main__":
    unittest.main()

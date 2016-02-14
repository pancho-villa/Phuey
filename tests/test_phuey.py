'''
Created on Jan 31, 2016

@author: pancho-villa
'''
import unittest
import logging
import sys
import phuey

from unittest.mock import patch
from http.client import HTTPConnection

__updated__ = "2016-02-13"

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
fmt = '%(levelname)s %(name)s - %(lineno)d - %(message)s'
formatter = logging.Formatter(fmt)
ch.setFormatter(formatter)
logger.addHandler(ch)


class PhueyTest(unittest.TestCase):

    def setUp(self):
        self.ip = '192.168.1.250'
        self.user = '23c05db12a8212d7c359e528b19f0b'
#         self.bridge = phuey.Bridge(self.ip, self.user)
        self.group_attrs = {'name': 'test groupie!'}

#     def test_change_colormode_on_LCT001(self):
#         """change light colormode and verifies it returns correct colormode"""
#         for mode in ['hue', 'xy', 'ct']:
#             for light in self.bridge.lights:
#                 if light.modelid is "LCT001":
#                     light.on = True
#                     if mode == 'ct':
#                         light.ct = 500
#                     elif mode == 'hue':
#                         light.hue = 18000
#                         light.sat = 254
#                     else:
#                         light.xy = [0.1691, 0.0441]
#                     self.assertEqual(light.colormode, mode)
# 
#     def test_change_colormode_on_non_LCT001_models_using_state(self):
#         """changing light colormode on white only bulbs using state should
#         fail"""
#         for light in self.bridge.lights:
#             if light.modelid != "LCT001":
#                 with self.assertRaises(AttributeError):
#                     light.state = {'ct': 500}
# 
#     def test_change_colormode_on_non_LCT001_models_using_attribute(self):
#         """changing light colormode on white only bulbs using color mode should
#         fail"""
#         for light in self.bridge.lights:
#             if light.modelid != "LCT001":
#                 with self.assertRaises(AttributeError):
#                     light.hue = 1

    @patch('phuey.http_client.HTTPResponse')
    def test_create_existing_group(self, mock_response):
        """create a group using an id not in use """
        mock_bridge_resp = b'[{"error":{"type":3,"address":"/groups/15","description":"resource, /groups/15, not available"}}]'
        mock_response.return_value.get_response.return_value.status.return_value = 200
        mock_response.return_value.get_response.return_value.read.return_value = mock_bridge_resp
        with self.assertRaises(AttributeError):
            g = phuey.Group(self.ip, self.user, 15)
            g.on = True

#     def test_change_existing_light(self):
#         pass

if __name__ == "__main__":
    unittest.main()

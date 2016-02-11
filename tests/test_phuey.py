'''
Created on Jan 31, 2016

@author: pancho-villa
'''
import sys
import unittest
import logging
import json

from phuey import phuey


class PhueyTest(unittest.TestCase):

    def setUp(self):
        self.ip = '192.168.0.100'
        self.user = 'workdesktop'
        self.logger = logging.getLogger()
        log_level = logging.DEBUG
        self.logger.setLevel(log_level)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(log_level)
        fmt = '%(levelname)s %(name)s - %(asctime)s - %(lineno)d - %(message)s'
        formatter = logging.Formatter(fmt)
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

    def tearDown(self):
        pass

#     def test_create_scene(self):
#         scene = phuey.Scene(self.ip, self.user, 'testy')
#         print(scene)

#     def test_create_group(self):
#         group = phuey.Group(self.ip, self.user, 11)
#
    def test_create_light_without_state(self):
        """creation should fail sine there isn't a state being passed in"""
        start_state = json.dumps({'on': False})
        try:
            light = phuey.Light(self.ip, self.user, 3, 'butt', 123, start_state)
        except Exception as exc:
            self.logger.error(exc)

#     def test_create_Bridge(self):
#         bridge = phuey.Bridge(self.ip, self.user)
#         print(bridge)


if __name__ == "__main__":
    unittest.main()

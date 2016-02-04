'''
Created on Jan 31, 2016

@author: pancho-villa
'''
import sys
import unittest
import logging

from phuey import phuey


class PhueyTest(unittest.TestCase):

    def setUp(self):
        self.ip = '192.168.1.250'
        self.user = '23c05db12a8212d7c359e528b19f0b'

    def tearDown(self):
        pass

    def test_create_scene(self):
        scene = phuey.Scene(self.ip, self.user, 'testy')
        body = {"name":"test scene", "lights":["1","2", "3"]}

    def test_create_group(self):
        group = phuey.Group(self.ip, self.user, 11)

    def test_create_light(self):
        light = phuey.Light(self.ip, self.user, None, None, None)
#         print(light)

    def test_create_Bridge(self):
        bridge = phuey.Bridge(self.ip, self.user)
        print(bridge)


if __name__ == "__main__":
    unittest.main()

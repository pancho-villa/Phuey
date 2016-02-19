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

__updated__ = "2016-02-16"

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

    def tearDown(self):
        self.patcher.stop()

    def test_use_existing_group_without_id_in_use(self):
        """initialize a group using an id not in use"""
        mock_bridge_resp = bytes('[{"error":{"type":3,"address":"/groups/15","description":"resource, /groups/15, not available"}}]', 'utf-8')
        self.mock.return_value.status = 200
        self.mock.return_value.read.return_value = mock_bridge_resp
        with self.assertRaises(AttributeError) as ae:
            phuey.Group(self.ip, self.user, 15)
        logging.debug(ae.exception)
        self.mock.assert_any_call()

    def test_use_existing_group_with_id_in_use(self):
        """initialize a group using an id not in use"""
        mock_bridge_resp = '{"name":"Group 1","lights":["1","2","3"],"type":"LightGroup","action": {"on":true,"bri":207,"hue":13236,"sat":209,"effect":"none","xy":[0.5097,0.4151],"ct":459,"alert":"none","colormode":"xy"}}'
        self.mock.return_value.status = 200
        self.mock.return_value.read.return_value = bytes(mock_bridge_resp,
                                                         'utf-8')
        phuey.Group(self.ip, self.user, 15)
        self.mock.assert_any_call()

    def test_create_bridge(self):
        """Create a new bridge, ensure no errors raised"""
        mock_bridge_resp = '{"lights":{"1":{"state":{"on":true,"bri":254,"hue":12510,"sat":226,"effect":"none","xy":[0.5268,0.4133],"ct":497,"alert":"none","colormode":"ct","reachable":true},"type":"Extended color light","name":"kitchen 1","modelid":"LCT001","manufacturername":"Philips","uniqueid":"00:17:88:01:00:b6:dc:46-0b","swversion":"66013452"}},"groups":{"1":{"name":"kitchen","lights":["1","4"],"type":"LightGroup","action":{"on":true,"bri":254,"hue":12510,"sat":226,"effect":"none","xy":[0.5268,0.4133],"ct":497,"alert":"none","colormode":"ct"}}},"config":{"name":"Huey","zigbeechannel":25,"bridgeid":"001788FFFE103554","mac":"00:17:88:10:35:54","dhcp":true,"ipaddress":"192.168.1.250","netmask":"255.255.255.0","gateway":"192.168.1.1","proxyaddress":"none","proxyport":0,"UTC":"2016-02-14T22:34:00","localtime":"2016-02-14T14:34:00","timezone":"America/Los_Angeles","modelid":"BSB001","swversion":"01030262","apiversion":"1.11.0","swupdate":{"updatestate":0,"checkforupdate":false,"devicetypes":{"bridge":false,"lights":[],"sensors":[]},"url":"","text":"","notify":false},"linkbutton":false,"portalservices":true,"portalconnection":"connected","portalstate":{"signedon":true,"incoming":true,"outgoing":true,"communication":"disconnected"},"factorynew":false,"replacesbridgeid":null,"backup":{"status":"idle","errorcode":0}}}'
        self.mock.return_value.status = 200
        self.mock.return_value.read.return_value = bytes(mock_bridge_resp,
                                                         'utf-8')
        phuey.Bridge(self.ip, self.user)
        self.mock.assert_any_call()

    def test_create_bridge_with_missing_parameters(self):
        """Create a new bridge that fails without the proper attributes"""
        mock_bridge_resp = '[{"error": {"description": "unauthorized user", "type": 1, "address": "/"}}]'
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
        mock_bridge_resp = '''[{"error":{"type":5,"address":"/groups/lights","description":"invalid/missing parameters in body"}}]'''
        self.mock.return_value.status = 200
        self.mock.return_value.read.return_value = bytes(mock_bridge_resp,
                                                         'utf-8')
        attrs = {"name": "bootylicious"}
        with self.assertRaises(AttributeError) as ae:
            phuey.Group(self.ip, self.user, attributes=attrs)
        logging.debug(ae.exception)
        self.mock.assert_any_call()

    def test_create_group_with_correct_parameters(self):
        attrs = {"lights": ["1", "2"]}
        self.mock.return_value.status = 200
        self.mock.return_value.read.side_effect = [
                                                   bytes('[{"success":{"id":"16"}}]', 'utf-8'),
                                                   bytes('{"name":"Group 2","lights":["1","2"],"type":"LightGroup","action": {"on":true,"bri":254,"hue":14839,"sat":148,"effect":"none","xy":[0.4622,0.4111],"ct":372,"alert":"none","colormode":"ct"}}','utf-8')]
        phuey.Group(self.ip, self.user, attributes=attrs)
        self.mock.assert_any_call()

    def test_bad_request(self):
        self.mock.return_value.status = 666
        self.mock.return_value.read = None
        with self.assertRaises(RuntimeError):
            phuey.Group(self.ip, self.user, 0)

#     def test_delete_group_zero(self):
#         self.mock.return_value.status = 200
#         g = phuey.Group(self.ip, self.user, 0)
#         g.remove()

    def test_create_bridge_bad_user(self):
        self.mock.return_value.status = 200
        self.mock.return_value.read.return_value = bytes('[{"error":{"type":101,"address":"/","description":"link button not pressed"}}]', 'utf-8')
        with self.assertRaises(AttributeError):
            phuey.Bridge(self.ip, self.user, True)
        self.mock.assert_any_call()

if __name__ == "__main__":
    unittest.main()

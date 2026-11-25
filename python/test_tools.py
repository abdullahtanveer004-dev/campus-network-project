"""Unit tests for the Python tools.  Run:  python -m unittest test_tools.py"""

import unittest

from subnet_planner import network_info, prefix_for_hosts, vlsm_plan
from config_generator import router_config, switch_config


class TestSubnetPlanner(unittest.TestCase):
    def test_network_info(self):
        info = network_info("192.168.20.0/24")
        self.assertEqual(info["subnet_mask"], "255.255.255.0")
        self.assertEqual(info["wildcard_mask"], "0.0.0.255")
        self.assertEqual(info["broadcast"], "192.168.20.255")
        self.assertEqual(info["usable_hosts"], 254)

    def test_point_to_point_link(self):
        info = network_info("10.0.0.0/30")
        self.assertEqual(info["usable_hosts"], 2)
        self.assertEqual(info["first_host"], "10.0.0.1")

    def test_prefix_for_hosts(self):
        self.assertEqual(prefix_for_hosts(2), 30)
        self.assertEqual(prefix_for_hosts(50), 26)
        self.assertEqual(prefix_for_hosts(254), 24)
        self.assertEqual(prefix_for_hosts(255), 23)

    def test_vlsm_no_overlap(self):
        plan = vlsm_plan("192.168.0.0/22",
                         {"STUDENTS": 300, "LAB": 100, "ADMIN": 50, "SERVERS": 10})
        self.assertEqual(plan[0]["name"], "STUDENTS")
        self.assertEqual(plan[0]["prefix"], "/23")
        import ipaddress
        nets = [ipaddress.ip_network(p["network"] + p["prefix"]) for p in plan]
        for i, a in enumerate(nets):
            for b in nets[i + 1:]:
                self.assertFalse(a.overlaps(b))

    def test_vlsm_too_small(self):
        with self.assertRaises(ValueError):
            vlsm_plan("192.168.0.0/24", {"BIG": 500})


class TestConfigGenerator(unittest.TestCase):
    PLAN = {
        "router_name": "R1", "trunk_interface": "GigabitEthernet0/0",
        "dns_server": "192.168.40.10", "domain": "campus.local",
        "vlans": [
            {"id": 10, "name": "ADMIN", "network": "192.168.10.0/24", "dhcp": True},
            {"id": 99, "name": "MGMT", "network": "192.168.99.0/24", "native": True},
        ],
    }

    def test_router_config(self):
        cfg = router_config(self.PLAN)
        self.assertIn("encapsulation dot1Q 10\n", cfg)
        self.assertIn("encapsulation dot1Q 99 native", cfg)
        self.assertIn("ip address 192.168.10.1 255.255.255.0", cfg)
        self.assertIn("ip dhcp pool ADMIN", cfg)
        self.assertNotIn("ip dhcp pool MGMT", cfg)

    def test_switch_config(self):
        cfg = switch_config(self.PLAN)
        self.assertIn("switchport trunk allowed vlan 10,99", cfg)
        self.assertIn("switchport trunk native vlan 99", cfg)


if __name__ == "__main__":
    unittest.main()

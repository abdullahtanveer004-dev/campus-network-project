#!/usr/bin/env python3
"""
config_generator.py - Generate Cisco IOS configs from a JSON network plan.

Network engineers automate repetitive configs instead of typing them by hand.
This script reads network_plan.json and writes:
  * the router-on-a-stick subinterfaces + DHCP pools for the router
  * the VLAN + trunk section for the switch

Usage:
    python config_generator.py                     # uses network_plan.json
    python config_generator.py my_plan.json        # custom plan
Output files are written to ./generated/
"""

import ipaddress
import json
import sys
from pathlib import Path


def load_plan(path: Path) -> dict:
    with path.open() as f:
        plan = json.load(f)
    # validate early so mistakes are caught before pasting into a device
    seen_ids, seen_nets = set(), []
    for v in plan["vlans"]:
        if not 1 <= v["id"] <= 4094:
            raise ValueError(f"VLAN {v['id']} is out of range 1-4094")
        if v["id"] in seen_ids:
            raise ValueError(f"Duplicate VLAN id {v['id']}")
        net = ipaddress.ip_network(v["network"])
        for other in seen_nets:
            if net.overlaps(other):
                raise ValueError(f"{net} overlaps {other}")
        seen_ids.add(v["id"])
        seen_nets.append(net)
    return plan


def router_config(plan: dict) -> str:
    trunk = plan["trunk_interface"]
    excl = plan.get("dhcp_excluded_hosts", 10)
    lines = [f"hostname {plan['router_name']}", "!",
             f"interface {trunk}", " no ip address", " no shutdown", "!"]
    dhcp_lines = []

    for v in plan["vlans"]:
        net = ipaddress.ip_network(v["network"])
        gateway = next(net.hosts())
        native = " native" if v.get("native") else ""
        lines += [f"interface {trunk}.{v['id']}",
                  f" description VLAN{v['id']}-{v['name']}",
                  f" encapsulation dot1Q {v['id']}{native}",
                  f" ip address {gateway} {net.netmask}", "!"]
        if v.get("dhcp"):
            last_excl = net.network_address + excl
            dhcp_lines += [f"ip dhcp excluded-address {gateway} {last_excl}",
                           f"ip dhcp pool {v['name']}",
                           f" network {net.network_address} {net.netmask}",
                           f" default-router {gateway}",
                           f" dns-server {plan['dns_server']}",
                           f" domain-name {plan['domain']}", "!"]
    return "\n".join(lines + dhcp_lines + ["end"]) + "\n"


def switch_config(plan: dict) -> str:
    lines = []
    native = None
    for v in plan["vlans"]:
        lines += [f"vlan {v['id']}", f" name {v['name']}"]
        if v.get("native"):
            native = v["id"]
    allowed = ",".join(str(v["id"]) for v in plan["vlans"])
    lines += ["!", "interface GigabitEthernet0/1", " switchport mode trunk"]
    if native:
        lines.append(f" switchport trunk native vlan {native}")
    lines += [f" switchport trunk allowed vlan {allowed}", "!", "end"]
    return "\n".join(lines) + "\n"


def main() -> int:
    here = Path(__file__).parent
    plan_path = Path(sys.argv[1]) if len(sys.argv) > 1 else here / "network_plan.json"
    try:
        plan = load_plan(plan_path)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as err:
        print(f"Error reading plan: {err}")
        return 1

    out_dir = here / "generated"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "router_generated.txt").write_text(router_config(plan))
    (out_dir / "switch_generated.txt").write_text(switch_config(plan))

    print(f"Generated configs for {len(plan['vlans'])} VLANs:")
    print(f"  {out_dir / 'router_generated.txt'}")
    print(f"  {out_dir / 'switch_generated.txt'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

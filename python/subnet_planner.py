#!/usr/bin/env python3
"""
subnet_planner.py - Subnet calculator and VLSM planner.

Two modes:
  1) Info about one network:
       python subnet_planner.py info 192.168.20.0/24
  2) VLSM plan: split a block among departments by host count:
       python subnet_planner.py vlsm 192.168.0.0/22 ADMIN:50 STUDENTS:300 LAB:100 SERVERS:10

VLSM = Variable Length Subnet Masking: give each department the smallest
subnet that fits, starting with the largest department, so no addresses
are wasted.

Uses only the Python standard library (ipaddress module).
"""

import ipaddress
import math
import sys


def network_info(cidr: str) -> dict:
    """Return the key facts about a network, e.g. '192.168.20.0/24'."""
    net = ipaddress.ip_network(cidr, strict=False)
    hosts = list(net.hosts()) if net.prefixlen < 31 else list(net)
    return {
        "network": str(net.network_address),
        "prefix": f"/{net.prefixlen}",
        "subnet_mask": str(net.netmask),
        "wildcard_mask": str(net.hostmask),  # used in OSPF and ACLs
        "broadcast": str(net.broadcast_address),
        "first_host": str(hosts[0]),
        "last_host": str(hosts[-1]),
        "usable_hosts": len(hosts),
    }


def prefix_for_hosts(hosts_needed: int) -> int:
    """Smallest prefix length that gives at least `hosts_needed` usable hosts.

    Usable hosts = 2^(host bits) - 2  (network + broadcast addresses are reserved).
    """
    if hosts_needed < 1:
        raise ValueError("hosts_needed must be at least 1")
    host_bits = math.ceil(math.log2(hosts_needed + 2))
    return 32 - max(host_bits, 2)


def vlsm_plan(base_cidr: str, requirements: dict) -> list:
    """Allocate subnets from base_cidr for each {name: hosts_needed}.

    Largest requirement first, so each subnet lands on a valid boundary.
    Raises ValueError if the base block is too small.
    """
    base = ipaddress.ip_network(base_cidr, strict=False)
    plan = []
    next_addr = int(base.network_address)

    for name, hosts in sorted(requirements.items(), key=lambda kv: kv[1], reverse=True):
        prefix = prefix_for_hosts(hosts)
        size = 2 ** (32 - prefix)
        # align the start address to a multiple of the subnet size
        if next_addr % size:
            next_addr += size - (next_addr % size)
        subnet = ipaddress.ip_network(f"{ipaddress.ip_address(next_addr)}/{prefix}")
        if not subnet.subnet_of(base):
            raise ValueError(f"Not enough space in {base} for {name} ({hosts} hosts)")
        info = network_info(str(subnet))
        info.update({"name": name, "hosts_needed": hosts,
                     "gateway": info["first_host"]})
        plan.append(info)
        next_addr += size
    return plan


def print_info(cidr: str) -> None:
    info = network_info(cidr)
    width = max(len(k) for k in info)
    print(f"\n  Network information for {cidr}\n  " + "-" * 40)
    for key, value in info.items():
        print(f"  {key.replace('_', ' ').title():<{width + 2}} {value}")
    print()


def print_plan(base: str, plan: list) -> None:
    header = f"{'Name':<12}{'Needed':>7}{'Usable':>8}  {'Subnet':<20}{'Mask':<17}{'Gateway':<16}{'Broadcast':<16}"
    print(f"\n  VLSM plan for {base}\n  " + "-" * len(header))
    print("  " + header)
    print("  " + "-" * len(header))
    for p in plan:
        print(f"  {p['name']:<12}{p['hosts_needed']:>7}{p['usable_hosts']:>8}  "
              f"{p['network'] + p['prefix']:<20}{p['subnet_mask']:<17}"
              f"{p['gateway']:<16}{p['broadcast']:<16}")
    used = sum(p["usable_hosts"] + 2 for p in plan)
    total = ipaddress.ip_network(base, strict=False).num_addresses
    print(f"\n  Addresses used: {used} of {total} ({used / total:.0%})\n")


def main(argv: list) -> int:
    if len(argv) < 2 or argv[0] not in ("info", "vlsm"):
        print(__doc__)
        return 1
    try:
        if argv[0] == "info":
            print_info(argv[1])
        else:
            reqs = {}
            for item in argv[2:]:
                name, hosts = item.split(":")
                reqs[name.upper()] = int(hosts)
            if not reqs:
                raise ValueError("Give at least one NAME:HOSTS pair")
            print_plan(argv[1], vlsm_plan(argv[1], reqs))
    except ValueError as err:
        print(f"Error: {err}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

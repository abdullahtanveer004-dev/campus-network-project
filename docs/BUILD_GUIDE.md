# Step-by-Step Build Guide (Cisco Packet Tracer 8.x)

Time needed: about 1–2 hours. Save often (**Ctrl+S**) as `Campus-Network.pkt`.

---

## Step 1: Place the devices

| Qty | Device | Where in Packet Tracer | Name it |
|---|---|---|---|
| 3 | Router **2911** | Network Devices → Routers | R1-HQ, R2-BRANCH, ISP |
| 2 | Switch **2960-24TT** | Network Devices → Switches | SW1-HQ, SW2-BRANCH |
| 2 | Server-PT | End Devices | HQ-SERVER, INTERNET-SERVER |
| 8 | PC-PT | End Devices | ADMIN-PC1/2, STUDENT-PC1/2, LAB-PC1/2, BRANCH-PC1/2 |

Tip: To rename a device, click it → **Config** tab → **Display Name** and **Hostname**.

Arrange them like this:

```
                [INTERNET-SERVER]
                        |
                      [ISP]
                        |
 [BRANCH-PCs]--[SW2]--[R2-BRANCH]----[R1-HQ]
                                        |  (trunk)
                                     [SW1-HQ]
               ______________/   /     |     \    \______________
          [ADMIN-PCs]  [STUDENT-PCs] [LAB-PCs]  [HQ-SERVER]
```

## Step 2: Cable everything

Use **Copper Straight-Through** cables (the black solid line) for all connections:

| From | Port | To | Port |
|---|---|---|---|
| R1-HQ | G0/0 | SW1-HQ | G0/1 |
| R1-HQ | G0/1 | R2-BRANCH | G0/1 |
| R1-HQ | G0/2 | ISP | G0/0 |
| ISP | G0/1 | INTERNET-SERVER | Fa0 |
| R2-BRANCH | G0/0 | SW2-BRANCH | G0/1 |
| SW1-HQ | Fa0/1, Fa0/2 | ADMIN-PC1, ADMIN-PC2 | Fa0 |
| SW1-HQ | Fa0/6, Fa0/7 | STUDENT-PC1, STUDENT-PC2 | Fa0 |
| SW1-HQ | Fa0/11, Fa0/12 | LAB-PC1, LAB-PC2 | Fa0 |
| SW1-HQ | Fa0/20 | HQ-SERVER | Fa0 |
| SW2-BRANCH | Fa0/1, Fa0/2 | BRANCH-PC1, BRANCH-PC2 | Fa0 |

> Router-to-router: Packet Tracer accepts straight-through between 2911 Gig ports (auto-MDIX).
> If a link stays red, use a **Copper Cross-Over** cable instead.

## Step 3: Configure the switches first

1. Click **SW1-HQ** → **CLI** tab → press Enter.
2. Type `enable` then `configure terminal`.
3. Copy everything from `configs/SW1-HQ.txt` and paste it (right-click → Paste).
4. Do the same for SW2-BRANCH with `configs/SW2-BRANCH.txt`.

## Step 4: Configure the routers

Paste `configs/R1-HQ.txt`, `configs/R2-BRANCH.txt` and `configs/ISP.txt` the same way.

> If `crypto key generate rsa ...` asks a question, type **1024** and press Enter.

## Step 5: Configure the servers and PCs

Follow `configs/SERVERS-and-PCs.md` (static IP + DNS + HTTP on the servers, DHCP on all PCs).

Wait about 30–60 seconds, or click **Fast Forward Time** (bottom-left) a few times, so that
OSPF, DHCP and STP can converge.

## Step 6: Test everything (and screenshot the results)

Run these from the PC's **Desktop → Command Prompt**:

| # | Test | From | Command | Expected result |
|---|---|---|---|---|
| 1 | DHCP works | any PC | `ipconfig` | Gets 192.168.x.11+ |
| 2 | Inter-VLAN routing | ADMIN-PC1 | `ping 192.168.20.11` | Replies |
| 3 | Branch reachability (OSPF) | LAB-PC1 | `ping 192.168.50.11` | Replies |
| 4 | Internet via NAT | BRANCH-PC1 | `ping 198.51.100.10` | Replies |
| 5 | DNS + Web | any PC | Web Browser → `www.campus.local` | HQ page loads |
| 6 | Internet web | any PC | Web Browser → `internet.com` | Internet page loads |
| 7 | **Security ACL** | STUDENT-PC1 | `ping 192.168.10.11` | **Fails** (Destination host unreachable) |
| 8 | SSH allowed | ADMIN-PC1 | `ssh -l admin 192.168.10.1` | Login with password `Admin@123` |
| 9 | SSH blocked | STUDENT-PC1 | `ssh -l admin 192.168.20.1` | Connection refused |

> The first ping often shows 1–2 timeouts while ARP resolves. That is normal, so ping again.

Useful verification commands on the routers and switches (screenshot these for GitHub):

```
show ip interface brief        ! all interfaces up/up?
show vlan brief                ! (SW1) VLANs and ports
show interfaces trunk          ! (SW1) trunk on Gi0/1
show ip route                  ! O = OSPF routes, O*E2 = default route on R2
show ip ospf neighbor          ! R1 and R2 should be FULL
show ip dhcp binding           ! which PC got which IP
show ip nat translations       ! (R1) after pinging the Internet
show access-lists              ! counters increase when students are blocked
show port-security             ! (SW1)
```

## Step 7: Troubleshooting

| Problem | Likely cause | Fix |
|---|---|---|
| PC gets 169.254.x.x | No DHCP reply | Check `show interfaces trunk` on SW1, and check that R1 G0/0 is `no shutdown` |
| VLANs can't ping each other | Wrong VLAN on a port or subinterface | `show vlan brief` and `show ip int brief` |
| Branch can't reach HQ | OSPF not up | `show ip ospf neighbor`: R1 G0/1 and R2 G0/1 must be in the same /30 |
| No Internet | NAT | Ping again, then check `show ip nat translations` and `ip nat inside/outside` |
| Web page won't load by name | DNS | Check the PC's DNS = 192.168.40.10 and that the DNS service on HQ-SERVER is On |

## Step 8: Save and export for GitHub

1. **File → Save As** → `Campus-Network.pkt` → put it in the root of this project folder.
2. Take screenshots (Windows: **Win+Shift+S**) of:
   - the full topology → `screenshots/topology.png`
   - successful pings → `screenshots/ping-tests.png`
   - the blocked student ping → `screenshots/acl-blocked.png`
   - `show ip ospf neighbor` and `show ip route` → `screenshots/ospf.png`
3. Upload the folder to GitHub (see the main README).

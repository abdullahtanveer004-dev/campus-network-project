# Server and PC Settings (set in the GUI, not the CLI)

## HQ-SERVER (Server-PT, connected to SW1 Fa0/20)

**Desktop → IP Configuration (Static)**

| Field | Value |
|---|---|
| IP Address | 192.168.40.10 |
| Subnet Mask | 255.255.255.0 |
| Default Gateway | 192.168.40.1 |
| DNS Server | 192.168.40.10 |

**Services → DNS** → turn **On**, then add these records (type A Record):

| Name | Address |
|---|---|
| www.campus.local | 192.168.40.10 |
| internet.com | 198.51.100.10 |

**Services → HTTP** → On. Edit `index.html` so it says something like
`<h1>Welcome to Campus Network - HQ Web Server</h1>`.

## INTERNET-SERVER (Server-PT, connected to ISP G0/1)

| Field | Value |
|---|---|
| IP Address | 198.51.100.10 |
| Subnet Mask | 255.255.255.0 |
| Default Gateway | 198.51.100.1 |

**Services → HTTP** → On. Edit `index.html`: `<h1>You reached the Internet!</h1>`

## All PCs and laptops

**Desktop → IP Configuration → choose DHCP.**
They should get an address like 192.168.20.11 automatically. If you see
169.254.x.x, DHCP failed (check the trunk and the subinterfaces).

| Device | Connect to | Expected network |
|---|---|---|
| ADMIN-PC1, ADMIN-PC2 | SW1 Fa0/1, Fa0/2 | 192.168.10.0/24 |
| STUDENT-PC1, STUDENT-PC2 | SW1 Fa0/6, Fa0/7 | 192.168.20.0/24 |
| LAB-PC1, LAB-PC2 | SW1 Fa0/11, Fa0/12 | 192.168.30.0/24 |
| BRANCH-PC1, BRANCH-PC2 | SW2 Fa0/1, Fa0/2 | 192.168.50.0/24 |

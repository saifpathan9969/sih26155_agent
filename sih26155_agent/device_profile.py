"""
Layered Device Profiling
========================
Replaces the single flat ``device_type`` label with a hierarchy, because
"router vs switch" was never one question:

    Raw configuration
          |
          +-- Vendor            (who made it)          <- fingerprint.py
          +-- Platform / OS     (what software)
          +-- Model             (which hardware)
          +-- Device class      (what kind of box)
          +-- Capabilities      (what it can do)
          +-- Network role      (how it is deployed)

WHY THIS EXISTS
---------------
The previous classifier inferred ``device_type = router`` from the presence of
``router bgp``. That is wrong. An Aruba CX 8325 is a **switch** at the hardware
level that performs a **core routing role** at the network level, and it runs
BGP. Under the old model it had to be one or the other, so ~6% of samples were
scored as misclassifications when the classifier was arguably right and the
single-label ground truth was the thing that could not express reality.

Three rules follow from that:

1. **A routing protocol is a capability, never a device class.** ``has_bgp()``
   adds ``BGP`` to capabilities and contributes to *role* inference only.
2. **Model identity outranks syntax.** If the config names its hardware, the
   model registry decides the device class; structural evidence is a fallback.
3. **Ambiguity is a first-class answer.** When evidence does not uniquely
   identify the hardware class, say so and let the existing human-review
   workflow handle it, rather than emitting a confident guess.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Level 2 — Device class (physical / product family)
# ---------------------------------------------------------------------------

class DeviceClass:
    ROUTER = "router"
    NETWORK_SWITCH = "network_switch"
    FIREWALL = "firewall"
    WIRELESS_AP = "wireless_ap"
    WIRELESS_CONTROLLER = "wireless_controller"
    LOAD_BALANCER = "load_balancer"
    SECURITY_APPLIANCE = "security_appliance"
    IOT_GATEWAY = "iot_gateway"
    IOT_CONTROLLER = "iot_controller"      # PLC / DCS / BMS controller
    IOT_ENDPOINT = "iot_endpoint"          # camera / sensor / smart device
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Level 3 — Network role (how the device is deployed)
# ---------------------------------------------------------------------------

class NetworkRole:
    CORE = "core"
    DISTRIBUTION = "distribution"
    ACCESS = "access"
    EDGE = "edge"
    WAN = "wan"
    INTERNET_GATEWAY = "internet_gateway"
    DC_LEAF = "dc_leaf"
    DC_SPINE = "dc_spine"
    BRANCH = "branch"
    WIRELESS_ACCESS = "wireless_access"
    PERIMETER = "perimeter"
    SEGMENTATION = "segmentation"
    OT_CELL = "ot_cell"
    BUILDING_AUTOMATION = "building_automation"
    IOT_EDGE = "iot_edge"
    UNKNOWN = "unknown"


# Coarse grouping retained for the Devices-page badge.
class AssetGroup:
    NETWORK = "network"
    SECURITY = "security"
    IOT = "iot"
    UNKNOWN = "unknown"


DEVICE_CLASS_DISPLAY: Dict[str, str] = {
    DeviceClass.ROUTER: "Router",
    DeviceClass.NETWORK_SWITCH: "Switch",
    DeviceClass.FIREWALL: "Firewall",
    DeviceClass.WIRELESS_AP: "Wireless AP",
    DeviceClass.WIRELESS_CONTROLLER: "Wireless Controller",
    DeviceClass.LOAD_BALANCER: "Load Balancer",
    DeviceClass.SECURITY_APPLIANCE: "Security Appliance",
    DeviceClass.IOT_GATEWAY: "IoT Gateway",
    DeviceClass.IOT_CONTROLLER: "Industrial Controller",
    DeviceClass.IOT_ENDPOINT: "IoT Endpoint",
    DeviceClass.UNKNOWN: "Unidentified",
}

NETWORK_ROLE_DISPLAY: Dict[str, str] = {
    NetworkRole.CORE: "Core",
    NetworkRole.DISTRIBUTION: "Distribution",
    NetworkRole.ACCESS: "Access",
    NetworkRole.EDGE: "Edge",
    NetworkRole.WAN: "WAN",
    NetworkRole.INTERNET_GATEWAY: "Internet Gateway",
    NetworkRole.DC_LEAF: "Data Centre Leaf",
    NetworkRole.DC_SPINE: "Data Centre Spine",
    NetworkRole.BRANCH: "Branch",
    NetworkRole.WIRELESS_ACCESS: "Wireless Access",
    NetworkRole.PERIMETER: "Perimeter",
    NetworkRole.SEGMENTATION: "Internal Segmentation",
    NetworkRole.OT_CELL: "OT Cell / Plant Floor",
    NetworkRole.BUILDING_AUTOMATION: "Building Automation",
    NetworkRole.IOT_EDGE: "IoT Edge",
    NetworkRole.UNKNOWN: "Undetermined",
}

DEVICE_CLASS_ICON: Dict[str, str] = {
    DeviceClass.ROUTER: "\U0001F6F0",
    DeviceClass.NETWORK_SWITCH: "\U0001F500",
    DeviceClass.FIREWALL: "\U0001F6E1",
    DeviceClass.WIRELESS_AP: "\U0001F4F6",
    DeviceClass.WIRELESS_CONTROLLER: "\U0001F4E1",
    DeviceClass.LOAD_BALANCER: "\u2696",
    DeviceClass.SECURITY_APPLIANCE: "\U0001F510",
    DeviceClass.IOT_GATEWAY: "\U0001F517",
    DeviceClass.IOT_CONTROLLER: "\u2699",
    DeviceClass.IOT_ENDPOINT: "\U0001F4F7",
    DeviceClass.UNKNOWN: "\u2753",
}

DEVICE_CLASS_TO_GROUP: Dict[str, str] = {
    DeviceClass.ROUTER: AssetGroup.NETWORK,
    DeviceClass.NETWORK_SWITCH: AssetGroup.NETWORK,
    DeviceClass.LOAD_BALANCER: AssetGroup.NETWORK,
    DeviceClass.WIRELESS_CONTROLLER: AssetGroup.NETWORK,
    DeviceClass.FIREWALL: AssetGroup.SECURITY,
    DeviceClass.SECURITY_APPLIANCE: AssetGroup.SECURITY,
    DeviceClass.WIRELESS_AP: AssetGroup.IOT,
    DeviceClass.IOT_GATEWAY: AssetGroup.IOT,
    DeviceClass.IOT_CONTROLLER: AssetGroup.IOT,
    DeviceClass.IOT_ENDPOINT: AssetGroup.IOT,
    DeviceClass.UNKNOWN: AssetGroup.UNKNOWN,
}

ASSET_GROUP_DISPLAY: Dict[str, str] = {
    AssetGroup.NETWORK: "Network Config",
    AssetGroup.SECURITY: "Firewall / Security Config",
    AssetGroup.IOT: "IoT Device Config",
    AssetGroup.UNKNOWN: "Unclassified Config",
}


# ---------------------------------------------------------------------------
# Capabilities — what the configuration proves the device can do
# ---------------------------------------------------------------------------
# Detected independently of device class. BGP lives here and ONLY here; it
# informs role inference but can never by itself make something a router.

CAPABILITY_SIGNALS: Dict[str, re.Pattern] = {
    "BGP": re.compile(r"\brouter\s+bgp\b|\bprotocols\s+bgp\b|\bbgp\s+system-as\b|\bbgp\s+\d+\b|\bneighbor\s+\S+\s+remote-as\b|\bpeer\s+\S+\s+as-number\b", re.I),
    "OSPF": re.compile(r"\brouter\s+ospf\b|\bprotocols\s+ospf\b|\bospf\s+\d+\b|\barea\s+[\d.]+\b", re.I),
    "ISIS": re.compile(r"\brouter\s+isis\b|\bprotocols\s+isis\b|\bisis\s+instance\b", re.I),
    "EIGRP": re.compile(r"\brouter\s+eigrp\b", re.I),
    "RIP": re.compile(r"\brouter\s+rip\b", re.I),
    "STATIC_ROUTING": re.compile(r"\bip\s+route\s+\d|\bip\s+route-static\b|\bstatic\s+route\b|\bset\s+protocols\s+static\b|/ip\s+route\s+add|\bip\s+route\s+0\.0\.0\.0\b", re.I),
    "MPLS": re.compile(r"\bmpls\s+(?:ip|ldp|label)\b|\bprotocols\s+mpls\b|\bmpls\s+ldp\b", re.I),
    "VRF": re.compile(r"\bip\s+vrf\b|\bvrf\s+(?:definition|forwarding|context)\b|\brouting-instances\b|\bvrf\s+default\b", re.I),
    "VXLAN_EVPN": re.compile(r"\bvxlan\b|\bnve\s+interface\b|\bevpn\b|\bl2vpn\s+evpn\b", re.I),
    "L2_SWITCHING": re.compile(r"\bswitchport\b|\bfamily\s+ethernet-switching\b|\bvlan\s+(?:access|trunk|database|batch)\b|\bmac\s*-?\s*address-table\b", re.I),
    "VLAN": re.compile(r"^\s*vlan\s+\d+|\binterface\s+vlan\s*\d+|\bset\s+vlans\b|\bcreate\s+vlan\b|\bconfigure\s+vlan\b", re.I | re.M),
    "STP": re.compile(r"\bspanning-tree\b|\bmstp\b|\brstp\b|\bstp\s+(?:enable|mode)\b|\benable\s+stpd\b", re.I),
    "PORT_SECURITY": re.compile(r"\bport-security\b|\bport\s+security\b|\bdot1x\b|\b802\.1x\b|\bieee8021x\b", re.I),
    "DHCP_SNOOPING": re.compile(r"\bdhcp\s+snooping\b|\bdhcp-snooping\b|\barp\s+inspection\b|\barp-protect\b", re.I),
    "LINK_AGGREGATION": re.compile(r"\bport-channel\b|\bchannel-group\b|\blacp\b|\bae\d+\b|\bbond\d+\b", re.I),
    "NAT": re.compile(r"\bnat\s+(?:inside|outside|source|destination|pool|rule)\b|\bip\s+nat\b|action=masquerade|\bsrcnat\b|\bmasquerade\b", re.I),
    "IPSEC_VPN": re.compile(r"\bcrypto\s+(?:isakmp|ipsec|map)\b|\bike(?:v2)?\s+\w+\b|\bipsec\s+(?:vpn|policy|proposal)\b|\bsecurity\s+ipsec\b|\bwireguard\b", re.I),
    "SSL_VPN": re.compile(r"\bssl-?vpn\b|\banyconnect\b|\bwebvpn\b", re.I),
    "STATEFUL_POLICY": re.compile(r"\bconfig\s+firewall\s+policy\b|\bset\s+rulebase\s+security\s+rules\b|\bset\s+security\s+policies\b|\bfrom-zone\b|\bsecurity-zone\b|\bnameif\b|\bzone\s+(?:trust|untrust|lan|wan)\b|connection-state=established", re.I),
    "THREAT_PREVENTION": re.compile(r"\butm-status\b|\bips-sensor\b|\bav-profile\b|\bintrusion-policy\b|\bthreat-prevention\b|\bwebfilter\b|\bweb-filter\b|\bantivirus\b|\bprofiles\s+vulnerability\b|\bmode\s+prevent\b", re.I),
    "WIRELESS_RADIO": re.compile(r"\bdot11(?:radio)?\b|\b802\.11[abgnacax]+\b|\bradio\s+(?:profile|\d|enable|2\.4|5)\b|/interface\s+wireless|\bieee_mode\b|\bradio_table\b|\bcaps-man\b", re.I),
    "WIRELESS_SSID": re.compile(r"\bssid\b|\bwlan\s+\S+|\bwlans\b|\bwlanconf\b", re.I),
    "WPA_ENTERPRISE": re.compile(r"\bwpa[23]?-enterprise\b|\bakm\s+(?:dot1x|sae)\b|\bauth.*\btype.*\beap\b|\bdot1x\s+authentication\b|\bsecurity\s+dot1x\b", re.I),
    "QOS": re.compile(r"\bservice-policy\b|\bpolicy-map\b|\bclass-of-service\b|\bqos\b|\btraffic-class\b", re.I),
    "MULTICAST": re.compile(r"\bip\s+pim\b|\bigmp\b|\bmsdp\b|\bprotocols\s+pim\b", re.I),
    "HA_CLUSTERING": re.compile(r"\bhsrp\b|\bvrrp\b|\bglbp\b|\bstackwise\b|\bredundancy\b|\bcluster\b|\bvsx\b|\bmlag\b|\bvpc\s+domain\b|\bha\s+(?:group|peer)\b", re.I),
    "MODBUS": re.compile(r"\bmodbus\b", re.I),
    "BACNET": re.compile(r"\bbacnet\b", re.I),
    "OPC_UA": re.compile(r"\bopc[\s-]?ua\b", re.I),
    "DNP3": re.compile(r"\bdnp3\b", re.I),
    "PROFINET": re.compile(r"\bprofinet\b", re.I),
    "ETHERNET_IP": re.compile(r"\bethernet[\s/-]?ip\b|\bcipsecurity\b", re.I),
    "MQTT": re.compile(r"\bmqtt\b|\bmosquitto\b", re.I),
    "COAP": re.compile(r"\bcoap\b|\blwm2m\b", re.I),
    "ZIGBEE": re.compile(r"\bzigbee\b|\bz-wave\b", re.I),
    "LORAWAN": re.compile(r"\blorawan?\b", re.I),
    "RTSP_ONVIF": re.compile(r"\brtsp\b|\bonvif\b", re.I),
    "CELLULAR_WAN": re.compile(r"\bcgdcont\b|\bapn\b|\blte\b|\b(?:4g|5g)\b|\bsim\s+\d\b|\bqflock\b", re.I),
}

# Capabilities that establish the device forwards at layer 3.
_L3_CAPABILITIES = {"BGP", "OSPF", "ISIS", "EIGRP", "RIP", "STATIC_ROUTING", "MPLS", "VRF"}
# Capabilities that establish it bridges at layer 2.
_L2_CAPABILITIES = {"L2_SWITCHING", "VLAN", "STP", "PORT_SECURITY", "DHCP_SNOOPING"}


# ---------------------------------------------------------------------------
# Model registry — authoritative device_class when the hardware is named
# ---------------------------------------------------------------------------
# (model regex, device_class, typical_role, l3_capable, canonical model label)
# Ordered most-specific first. This table encodes product knowledge that cannot
# be recovered from syntax: a Catalyst 9300 and an ASR 1001 can carry nearly
# identical IOS configuration yet are different classes of hardware.

ModelRule = Tuple[re.Pattern, str, str, bool, str]

MODEL_REGISTRY: List[ModelRule] = [
    # --- Aruba / HPE AOS-CX ------------------------------------------------
    (re.compile(r"\b(?:cx[\s-]?)?(?:8400|9300|10000)\b", re.I), DeviceClass.NETWORK_SWITCH, NetworkRole.CORE, True, "Aruba CX Core"),
    (re.compile(r"\b(?:cx[\s-]?)?(?:8320|8325|8360)\b", re.I), DeviceClass.NETWORK_SWITCH, NetworkRole.DC_LEAF, True, "Aruba CX 83xx"),
    (re.compile(r"\b(?:cx[\s-]?)?6400\b", re.I), DeviceClass.NETWORK_SWITCH, NetworkRole.DISTRIBUTION, True, "Aruba CX 6400"),
    (re.compile(r"\b(?:cx[\s-]?)?(?:6100|6200|6300)\b", re.I), DeviceClass.NETWORK_SWITCH, NetworkRole.ACCESS, True, "Aruba CX 62xx/63xx"),
    (re.compile(r"\b(?:2930f|3810m|5400r)\b", re.I), DeviceClass.NETWORK_SWITCH, NetworkRole.ACCESS, True, "Aruba AOS-S"),
    (re.compile(r"\bap(?:1[0-9]{2}|2[0-9]{2}|5[0-9]{2}|6[0-9]{2})\b|\binstant\s+ap\b", re.I), DeviceClass.WIRELESS_AP, NetworkRole.WIRELESS_ACCESS, False, "Aruba AP"),
    # --- Cisco -------------------------------------------------------------
    (re.compile(r"\bcatalyst\s*9[456]\d\d\b|\bc9[456]\d\d\b", re.I), DeviceClass.NETWORK_SWITCH, NetworkRole.CORE, True, "Catalyst 94xx-96xx"),
    (re.compile(r"\bcatalyst\s*9[23]\d\d\b|\bc9[23]\d\d\b|\bws-c3(?:650|850)\b|\b3850\b|\b9300\b|\b9200\b", re.I), DeviceClass.NETWORK_SWITCH, NetworkRole.ACCESS, True, "Catalyst 92xx/93xx"),
    (re.compile(r"\bws-c2960\b|\b2960\b|\b3560\b", re.I), DeviceClass.NETWORK_SWITCH, NetworkRole.ACCESS, True, "Catalyst 2960/3560"),
    (re.compile(r"\bn9k-c95\d\d\b|\bnexus\s*95\d\d\b|\bnexus\s*7\d\d\d\b", re.I), DeviceClass.NETWORK_SWITCH, NetworkRole.DC_SPINE, True, "Nexus 95xx/7xxx"),
    (re.compile(r"\bn9k\b|\bnexus\s*9[23]\d\d\b|\bnexus\s*3\d\d\d\b|\bnexus\s*9300\b", re.I), DeviceClass.NETWORK_SWITCH, NetworkRole.DC_LEAF, True, "Nexus 93xx"),
    (re.compile(r"\basr\s*9\d\d\d\b|\bncs\s*\d\d\d\d\b", re.I), DeviceClass.ROUTER, NetworkRole.CORE, True, "Cisco ASR 9000 / NCS"),
    (re.compile(r"\basr\s*10\d\d\b|\basr1001\b|\basr1002\b", re.I), DeviceClass.ROUTER, NetworkRole.WAN, True, "Cisco ASR 1000"),
    (re.compile(r"\bisr\s*4\d\d\d\b|\bisr4331\b|\bisr\s*1\d\d\d\b|\bc88\d\d\b", re.I), DeviceClass.ROUTER, NetworkRole.BRANCH, True, "Cisco ISR"),
    (re.compile(r"\basa\s*5\d\d\d\b|\basa\s+version\b|\bfpr\s*\d\d\d\d\b|\bfirepower\b", re.I), DeviceClass.FIREWALL, NetworkRole.PERIMETER, True, "Cisco ASA / Firepower"),
    (re.compile(r"\bair-ap\b|\bc91[0-9]{2}\b|\bap\s*38\d\d\b|\baironet\b", re.I), DeviceClass.WIRELESS_AP, NetworkRole.WIRELESS_ACCESS, False, "Cisco Aironet / CW"),
    (re.compile(r"\bwlc\b|\bc9800\b|\bair-ct\d\d\d\d\b|\b(?:3504|5520|8540)\b", re.I), DeviceClass.WIRELESS_CONTROLLER, NetworkRole.WIRELESS_ACCESS, True, "Cisco WLC"),
    (re.compile(r"\bmeraki\b|\bmx\d\d\b|\bms\d\d\d\b|\bmr\d\d\b", re.I), DeviceClass.NETWORK_SWITCH, NetworkRole.ACCESS, True, "Cisco Meraki"),
    # --- Juniper -----------------------------------------------------------
    (re.compile(r"\bptx\s*\d+\b", re.I), DeviceClass.ROUTER, NetworkRole.CORE, True, "Juniper PTX"),
    (re.compile(r"\bmx\s*\d+\b|\bmx\s*series\b|\bmxseries\b", re.I), DeviceClass.ROUTER, NetworkRole.EDGE, True, "Juniper MX"),
    (re.compile(r"\bacx\s*\d+\b", re.I), DeviceClass.ROUTER, NetworkRole.ACCESS, True, "Juniper ACX"),
    (re.compile(r"\bqfx\s*\d+\b", re.I), DeviceClass.NETWORK_SWITCH, NetworkRole.DC_LEAF, True, "Juniper QFX"),
    (re.compile(r"\bex\s*\d{4}\b", re.I), DeviceClass.NETWORK_SWITCH, NetworkRole.ACCESS, True, "Juniper EX"),
    (re.compile(r"\bsrx\s*\d+\b", re.I), DeviceClass.FIREWALL, NetworkRole.PERIMETER, True, "Juniper SRX"),
    (re.compile(r"\bap4[35]\b|\bmist\b", re.I), DeviceClass.WIRELESS_AP, NetworkRole.WIRELESS_ACCESS, False, "Juniper Mist AP"),
    # --- Arista ------------------------------------------------------------
    (re.compile(r"\bdcs-7[358]\d\d\b|\b7(?:280|300|500|800)\b", re.I), DeviceClass.NETWORK_SWITCH, NetworkRole.DC_SPINE, True, "Arista 7280+"),
    (re.compile(r"\bdcs-70\d\d\b|\b70(?:20|50|60)\b", re.I), DeviceClass.NETWORK_SWITCH, NetworkRole.DC_LEAF, True, "Arista 70xx"),
    # --- Firewalls ---------------------------------------------------------
    (re.compile(r"\bfortigate\b|\bfg-\d+\b|\bfgt\b", re.I), DeviceClass.FIREWALL, NetworkRole.PERIMETER, True, "FortiGate"),
    (re.compile(r"\bfortiswitch\b|\bfs-\d+\b", re.I), DeviceClass.NETWORK_SWITCH, NetworkRole.ACCESS, True, "FortiSwitch"),
    (re.compile(r"\bfortiap\b|\bfap-\d+\b", re.I), DeviceClass.WIRELESS_AP, NetworkRole.WIRELESS_ACCESS, False, "FortiAP"),
    (re.compile(r"\bpa-\d+\b|\bpan-os\b|\bpanorama\b", re.I), DeviceClass.FIREWALL, NetworkRole.PERIMETER, True, "Palo Alto PA"),
    (re.compile(r"\bfirebox\b", re.I), DeviceClass.FIREWALL, NetworkRole.PERIMETER, True, "WatchGuard Firebox"),
    (re.compile(r"\bcloudgen\b|\bbarracuda\b", re.I), DeviceClass.FIREWALL, NetworkRole.PERIMETER, True, "Barracuda CloudGen"),
    (re.compile(r"\bsonicwall\b|\btz\d+\b|\bnsa\s*\d+\b", re.I), DeviceClass.FIREWALL, NetworkRole.PERIMETER, True, "SonicWall"),
    (re.compile(r"\bngaf\b|\bsangfor\b", re.I), DeviceClass.FIREWALL, NetworkRole.PERIMETER, True, "Sangfor NGAF"),
    (re.compile(r"\bstoneos\b|\bhillstone\b", re.I), DeviceClass.FIREWALL, NetworkRole.PERIMETER, True, "Hillstone"),
    (re.compile(r"\bforcepoint\b|\bngfw\b", re.I), DeviceClass.FIREWALL, NetworkRole.PERIMETER, True, "Forcepoint NGFW"),
    (re.compile(r"\bgaia\b|\bcheck\s*point\b", re.I), DeviceClass.FIREWALL, NetworkRole.PERIMETER, True, "Check Point"),
    # Anchored to product/appliance strings, not the bare vendor name: a bare
    # "sophos" matched the SSID "Sophos-Open" on a Sophos *access point* and
    # misfiled it as a firewall.
    (re.compile(r"\bpfsense\b|\bopnsense\b|\bkerio\s+control\b|\bsophos\s+(?:xg|sfos|firewall)\b"
                r"|\bxgs\d+\b|\bsg\d+\s+firewall\b", re.I),
     DeviceClass.FIREWALL, NetworkRole.PERIMETER, True, "Open-source / Sophos FW"),
    # --- Load balancer -----------------------------------------------------
    (re.compile(r"\bbig-?ip\b|\bviprion\b|\btmos\b|\bltm\b", re.I), DeviceClass.LOAD_BALANCER, NetworkRole.DISTRIBUTION, True, "F5 BIG-IP"),
    # --- Other network vendors --------------------------------------------
    (re.compile(r"\b7750\s*sr\b|\b7250\s*ixr\b|\bsr\s*os\b", re.I), DeviceClass.ROUTER, NetworkRole.CORE, True, "Nokia SR OS"),
    (re.compile(r"\bccr\d+\b|\brb\d+\b|\bhex\b", re.I), DeviceClass.ROUTER, NetworkRole.BRANCH, True, "MikroTik Router"),
    (re.compile(r"\bcrs\d+\b", re.I), DeviceClass.NETWORK_SWITCH, NetworkRole.ACCESS, True, "MikroTik CRS"),
    (re.compile(r"\bcap\s*ac\b|\bhap\b|\bcapsman\b", re.I), DeviceClass.WIRELESS_AP, NetworkRole.WIRELESS_ACCESS, False, "MikroTik Wireless"),
    (re.compile(r"\bar\s*(?:20|30|40)\d\d\b|\bar\d{3,4}\b", re.I), DeviceClass.ROUTER, NetworkRole.BRANCH, True, "Huawei AR"),
    (re.compile(r"\bs5\d\d\d\b|\bs6\d\d\d\b|\bs1\d\d\d\b|\bce\d\d\d\d\b", re.I), DeviceClass.NETWORK_SWITCH, NetworkRole.ACCESS, True, "Huawei S-series"),
    (re.compile(r"\bx4[46]0\b|\bx6\d\d\b|\bsummit\b", re.I), DeviceClass.NETWORK_SWITCH, NetworkRole.ACCESS, True, "Extreme Summit"),
    (re.compile(r"\bdgs-\d+\b|\bdxs-\d+\b", re.I), DeviceClass.NETWORK_SWITCH, NetworkRole.ACCESS, True, "D-Link DGS"),
    (re.compile(r"\bm4[35]00\b|\bprosafe\b|\bgs\d{3}\b", re.I), DeviceClass.NETWORK_SWITCH, NetworkRole.ACCESS, True, "NETGEAR ProSAFE"),
    (re.compile(r"\bedgerouter\b|\ber-\d+\b|\bedgeos\b", re.I), DeviceClass.ROUTER, NetworkRole.BRANCH, True, "Ubiquiti EdgeRouter"),
    (re.compile(r"\buap\b|\bunifi\s+ap\b|\bu6\b|\bnanohd\b", re.I), DeviceClass.WIRELESS_AP, NetworkRole.WIRELESS_ACCESS, False, "Ubiquiti UniFi AP"),
    (re.compile(r"\bicx\s*\d+\b|\bnetiron\b|\bfastiron\b", re.I), DeviceClass.NETWORK_SWITCH, NetworkRole.ACCESS, True, "Brocade/Ruckus ICX"),
    (re.compile(r"\bs\d\d\d\d-on\b|\bos10\b|\bn\d\d\d\d\b", re.I), DeviceClass.NETWORK_SWITCH, NetworkRole.DC_LEAF, True, "Dell OS10"),
    (re.compile(r"\beap\d+\b|\bomada\b|\bgwn7\d+\b|\bnwa\d+\b|\bcnpilot\b|\bews\d+\b|\bvigorap\b|\brg-ap\b", re.I), DeviceClass.WIRELESS_AP, NetworkRole.WIRELESS_ACCESS, False, "SMB Access Point"),
    # --- Industrial controllers (PLC / DCS / BMS) --------------------------
    (re.compile(r"\bs7-1[25]00\b|\bsimatic\b|\bcpu\s*15\d\d\b", re.I), DeviceClass.IOT_CONTROLLER, NetworkRole.OT_CELL, False, "Siemens SIMATIC S7"),
    (re.compile(r"\bm(?:580|340|241|251)\b|\bmodicon\b", re.I), DeviceClass.IOT_CONTROLLER, NetworkRole.OT_CELL, False, "Schneider Modicon"),
    (re.compile(r"\bcontrollogix\b|\bcompactlogix\b|\b55\d\d\b|\brslogix\b", re.I), DeviceClass.IOT_CONTROLLER, NetworkRole.OT_CELL, False, "Rockwell Logix"),
    (re.compile(r"\bmelsec\b|\biq-[rf]\b", re.I), DeviceClass.IOT_CONTROLLER, NetworkRole.OT_CELL, False, "Mitsubishi MELSEC"),
    (re.compile(r"\bsysmac\b|\bnj\d+\b|\bnx\d+\b", re.I), DeviceClass.IOT_CONTROLLER, NetworkRole.OT_CELL, False, "Omron Sysmac"),
    (re.compile(r"\bcx\d{4}\b|\btwincat\b|\bbeckhoff\b", re.I), DeviceClass.IOT_CONTROLLER, NetworkRole.OT_CELL, False, "Beckhoff TwinCAT"),
    (re.compile(r"\bpfc200\b|\bwago\b", re.I), DeviceClass.IOT_CONTROLLER, NetworkRole.OT_CELL, False, "WAGO PFC"),
    (re.compile(r"\baxc\s*f\b|\bplcnext\b", re.I), DeviceClass.IOT_CONTROLLER, NetworkRole.OT_CELL, False, "Phoenix Contact PLCnext"),
    (re.compile(r"\bac500\b|\brtu500\b", re.I), DeviceClass.IOT_CONTROLLER, NetworkRole.OT_CELL, False, "ABB AC500"),
    (re.compile(r"\bdeltav\b|\bovation\b", re.I), DeviceClass.IOT_CONTROLLER, NetworkRole.OT_CELL, False, "Emerson DeltaV"),
    (re.compile(r"\bmark\s*vie\b|\bpacsystems\b|\brx3i\b", re.I), DeviceClass.IOT_CONTROLLER, NetworkRole.OT_CELL, False, "GE PACSystems"),
    (re.compile(r"\bniagara\b|\bjace\b", re.I), DeviceClass.IOT_CONTROLLER, NetworkRole.BUILDING_AUTOMATION, False, "Honeywell Niagara"),
    (re.compile(r"\bmetasys\b|\bnae\b|\bsne\b", re.I), DeviceClass.IOT_CONTROLLER, NetworkRole.BUILDING_AUTOMATION, False, "Johnson Controls Metasys"),
    # --- IoT gateways ------------------------------------------------------
    (re.compile(r"\brut[xz]?\d+\b|\bteltonika\b|\brutos\b", re.I), DeviceClass.IOT_GATEWAY, NetworkRole.IOT_EDGE, True, "Teltonika RUT"),
    (re.compile(r"\bbg9\d\b|\bec2\d\b|\bquectel\b", re.I), DeviceClass.IOT_GATEWAY, NetworkRole.IOT_EDGE, True, "Quectel Modem"),
    (re.compile(r"\bnport\b|\beds-\d+\b|\bmoxa\b", re.I), DeviceClass.IOT_GATEWAY, NetworkRole.IOT_EDGE, True, "Moxa"),
    (re.compile(r"\bwise-\d+\b|\badam-\d+\b|\badvantech\b", re.I), DeviceClass.IOT_GATEWAY, NetworkRole.IOT_EDGE, True, "Advantech WISE"),
    (re.compile(r"\bopenwrt\b", re.I), DeviceClass.IOT_GATEWAY, NetworkRole.IOT_EDGE, True, "OpenWrt"),
    # --- IoT endpoints (cameras, sensors, smart devices) -------------------
    (re.compile(r"\bq3\d\b|\bp32\b|\baxis\b", re.I), DeviceClass.IOT_ENDPOINT, NetworkRole.IOT_EDGE, False, "Axis Camera"),
    (re.compile(r"\bds-2cd\b|\bhikvision\b", re.I), DeviceClass.IOT_ENDPOINT, NetworkRole.IOT_EDGE, False, "Hikvision Camera"),
    (re.compile(r"\bipc-h[fd]w\b|\bdahua\b", re.I), DeviceClass.IOT_ENDPOINT, NetworkRole.IOT_EDGE, False, "Dahua Camera"),
    (re.compile(r"\bwisenet\b|\bhanwha\b", re.I), DeviceClass.IOT_ENDPOINT, NetworkRole.IOT_EDGE, False, "Hanwha Wisenet"),
    (re.compile(r"\btasmota\b|\bsonoff\b", re.I), DeviceClass.IOT_ENDPOINT, NetworkRole.IOT_EDGE, False, "Tasmota Device"),
    (re.compile(r"\besp32\b|\besphome\b|\bespressif\b", re.I), DeviceClass.IOT_ENDPOINT, NetworkRole.IOT_EDGE, False, "Espressif ESP"),
    (re.compile(r"\bboron\b|\bphoton\b|\bparticle\b", re.I), DeviceClass.IOT_ENDPOINT, NetworkRole.IOT_EDGE, False, "Particle Device"),
    (re.compile(r"\bshelly\b", re.I), DeviceClass.IOT_ENDPOINT, NetworkRole.IOT_EDGE, False, "Shelly Device"),
]


# ---------------------------------------------------------------------------
# Structural device-class evidence (fallback when no model is named)
# ---------------------------------------------------------------------------
# Deliberately excludes routing protocols: those are capabilities. What
# distinguishes the hardware classes is the *forwarding and policy* constructs.

CLASS_STRUCTURAL_SIGNALS: Dict[str, List[Tuple[re.Pattern, float]]] = {
    DeviceClass.NETWORK_SWITCH: [
        (re.compile(r"\bswitchport\s+(?:mode|access|trunk)\b", re.I), 4.0),
        (re.compile(r"\bmac\s*-?\s*address-table\b", re.I), 4.0),
        (re.compile(r"\bspanning-tree\b|\benable\s+stpd\b", re.I), 3.0),
        (re.compile(r"\bfamily\s+ethernet-switching\b", re.I), 4.0),
        (re.compile(r"\bport-security\b|\bstorm-control\b|\bdhcp\s+snooping\b", re.I), 3.0),
        (re.compile(r"\bvlan\s+(?:access|trunk|batch)\b|\bconfigure\s+vlan\s+\S+\s+add\s+ports\b", re.I), 3.0),
        (re.compile(r"\binterface\s+(?:ethernet)?\s?\d+/\d+/\d+\b", re.I), 1.5),
        (re.compile(r"\bport-channel\b|\blacp\b", re.I), 1.0),
    ],
    DeviceClass.ROUTER: [
        # WAN-facing and provider constructs, not routing protocols
        (re.compile(r"\bencapsulation\s+(?:ppp|hdlc|frame-relay|dot1q)\b", re.I), 3.0),
        (re.compile(r"\binterface\s+(?:serial|atm|pos|dialer|cellular)\b", re.I), 4.0),
        (re.compile(r"\binterface\s+tengige\d+/\d+/\d+/\d+\b", re.I), 3.0),
        (re.compile(r"\binterface\s+ge-\d+/\d+/\d+\b", re.I), 2.0),
        (re.compile(r"\bip\s+vrf\s+forwarding\b|\baddress-family\s+vpnv4\b", re.I), 3.0),
        (re.compile(r"\bmpls\s+ldp\s+router-id\b", re.I), 3.0),
        (re.compile(r"\binterface\s+(?:Loopback|Tunnel)\d+", re.I), 1.0),
    ],
    DeviceClass.FIREWALL: [
        (re.compile(r"\bconfig\s+firewall\s+policy\b", re.I), 4.0),
        (re.compile(r"\bset\s+rulebase\s+security\s+rules\b", re.I), 4.0),
        (re.compile(r"\bset\s+security\s+(?:policies|zones)\b", re.I), 4.0),
        (re.compile(r"\bnameif\b|\bsecurity-level\b", re.I), 4.0),
        (re.compile(r"\bfrom-zone\b.*\bto-zone\b|\bzone-pair\b|\bsecurity-zone\b", re.I), 3.0),
        (re.compile(r"\butm-status\b|\bips-sensor\b|\bav-profile\b|\bwebfilter\b", re.I), 3.0),
        (re.compile(r"\bsource_zone\b|\bdest_zone\b|\bfirewall-rule\b", re.I), 3.0),
        (re.compile(r"\bpolicy-type\s+firebox\b|\bsystem\s+management\s+lockout\b", re.I), 3.0),
        (re.compile(r"\biptables\b|\bnftables\b|\bchain=(?:input|forward)\b", re.I), 2.0),
        (re.compile(r"\bdefault-action\s+'?drop'?\b|\boption\s+input\s+'DROP'\b", re.I), 2.0),
    ],
    DeviceClass.WIRELESS_AP: [
        (re.compile(r"\bdot11(?:radio)?\b|\b802\.11[abgnacax]+\b", re.I), 4.0),
        (re.compile(r"\bradio\s+(?:profile|\d|2\.4|5)\b|\bradio_table\b|\bieee_mode\b", re.I), 3.0),
        (re.compile(r"\bwpa[23]?(?:-personal|-enterprise|-psk)?\b", re.I), 3.0),
        (re.compile(r"/interface\s+wireless|\bcaps-man\b", re.I), 3.0),
        (re.compile(r"\bssid\b|\bwlans?\b", re.I), 2.0),
        (re.compile(r"\bband-steering\b|\bchannel-width\b|\btx-power\b|\bclient_isolation\b", re.I), 2.0),
    ],
    DeviceClass.WIRELESS_CONTROLLER: [
        (re.compile(r"\bcapwap\b|\bap-group\b|\bap\s+name\b", re.I), 4.0),
        (re.compile(r"\bwlan\s+\S+\s+\d+\s+\S+", re.I), 3.0),
        (re.compile(r"\bap\s+dot11\s+(?:5ghz|24ghz)\s+rrm\b", re.I), 4.0),
        (re.compile(r"\brogue\s+ap\b|\bzonedirector\b|\bsmartzone\b", re.I), 3.0),
    ],
    DeviceClass.LOAD_BALANCER: [
        (re.compile(r"\bltm\s+(?:virtual|pool|node)\b", re.I), 4.0),
        (re.compile(r"\bpersistence\s+(?:profile|cookie|source-addr)\b", re.I), 3.0),
        (re.compile(r"\bsnat\s+(?:automap|pool)\b", re.I), 3.0),
        (re.compile(r"\bhealth\s+monitor\b|\bmonitor\s+http\b", re.I), 2.0),
        (re.compile(r"\bhaproxy\b|\bupstream\s+\S+\s*\{", re.I), 2.0),
    ],
    DeviceClass.IOT_CONTROLLER: [
        (re.compile(r"\bprotectionlevel\b|\bsecurepgpccommunication\b", re.I), 4.0),
        (re.compile(r"\bcipsecurity\b|\brslogix5000project\b|\bfactorytalk\b", re.I), 4.0),
        (re.compile(r"\bslmpsecurity\b|\bsysmacsecurity\b|\bdeltavsecurity\b|\bmetasyssecurity\b", re.I), 4.0),
        (re.compile(r"\badssecurity\b|\btcconfig\b|\bmarkviepolicy\b|\babbconfiguration\b", re.I), 4.0),
        (re.compile(r"\bplcconfiguration\b|\bcybersecurityprofile\b", re.I), 4.0),
        (re.compile(r"\bmodbus\b|\bprofinet\b|\bdnp3\b|\bopc[\s-]?ua\b|\bbacnet\b", re.I), 2.0),
        (re.compile(r"\bwritelock\b|\bwrite_protect\b|\boperationrights\b", re.I), 2.0),
    ],
    DeviceClass.IOT_GATEWAY: [
        (re.compile(r"\buci\s+(?:set|commit)\b|\bpackage\s+(?:network|firewall)\b", re.I), 3.0),
        (re.compile(r"\bcgdcont\b|\bapn\b|\bqflock\b", re.I), 4.0),
        (re.compile(r"\bmqtt\b.*\bbroker\b|\bmodbus_tcp\b.*\bgateway\b", re.I), 3.0),
        (re.compile(r"\bdropbear\b|\buhttpd\b|\bbusybox\b", re.I), 2.0),
        (re.compile(r"\boption\s+proto\s+'?(?:static|dhcp)'?", re.I), 2.0),
    ],
    DeviceClass.IOT_ENDPOINT: [
        (re.compile(r"\bonvif\b|\brtsp\b", re.I), 4.0),
        (re.compile(r"\bmqtthost\b|\bwebpassword\b|\bsetoption\d*\b", re.I), 4.0),
        (re.compile(r"\besphome\b|\bfallback_hotspot\b", re.I), 4.0),
        (re.compile(r"\bserialnumber\b|\bdevicename\b|\bdeviceid\b", re.I), 2.0),
        (re.compile(r"\blorawan?\b|\bzigbee\b|\bdev_eui\b", re.I), 3.0),
        (re.compile(r"\bfirmware[_\s-]?version\b|\bsensor\b|\btelemetry\b", re.I), 1.5),
    ],
}

# Hard eligibility gates.
#
# Some classes have a defining construct without which they are simply not that
# class, and weight tuning alone could not express it. A switch config that
# names a VLAN "GUEST-WIFI", or a firewall carrying a guest-wireless policy,
# both mention an SSID — but neither has a radio. Requiring radio-layer
# evidence before a device can be called an access point removed a whole family
# of misclassifications that no amount of re-weighting had fixed.
CLASS_REQUIRED_SIGNALS: Dict[str, re.Pattern] = {
    DeviceClass.WIRELESS_AP: re.compile(
        r"\bdot11(?:radio)?\b|\b802\.11[abgnacax]+\b|\bradio\s*(?:profile|\d|2\.4|5|enable)\b"
        r"|\bradio_table\b|\bieee_mode\b|/interface\s+wireless|\bcaps-man\b"
        r"|\bchannel[-_\s]?width\b|\btx[-_\s]?power\b|\bband[-_\s]?steering\b"
        r"|\bwpa[23]?(?:-personal|-enterprise|-psk)?\b|\bwireless\.(?:radio|ssid)\b"
        r"|\bwlanconf\b|\"wlans\"|\bap-group\b|\bcapwap\b",
        re.I,
    ),
    DeviceClass.WIRELESS_CONTROLLER: re.compile(
        r"\bcapwap\b|\bap-group\b|\bap\s+name\b|\bap\s+dot11\b|\bzonedirector\b"
        r"|\bsmartzone\b|\brogue\s+ap\b|\bwlc\b",
        re.I,
    ),
    DeviceClass.LOAD_BALANCER: re.compile(
        r"\bltm\s+(?:virtual|pool|node)\b|\bvirtual\s+server\b|\bpool\s+member"
        r"|\bsnat\s+(?:automap|pool)\b|\bhaproxy\b|\bupstream\s+\S+\s*\{"
        r"|\bpersistence\b|\bbig-?ip\b",
        re.I,
    ),
    DeviceClass.IOT_CONTROLLER: re.compile(
        r"\bmodbus\b|\bprofinet\b|\bbacnet\b|\bdnp3\b|\bopc[\s-]?ua\b|\bethernet[\s/-]?ip\b"
        r"|\bprotectionlevel\b|\bcipsecurity\b|\bslmpsecurity\b|\bsysmacsecurity\b"
        r"|\bdeltavsecurity\b|\bmetasyssecurity\b|\badssecurity\b|\bmarkviepolicy\b"
        r"|\babbconfiguration\b|\bplcconfiguration\b|\bniagara\b|\bplc\b",
        re.I,
    ),
    DeviceClass.NETWORK_SWITCH: re.compile(
        r"\bswitchport\b|\bspanning-tree\b|\bmac\s*-?\s*address-table\b|\bvlan\b"
        r"|\bfamily\s+ethernet-switching\b|\bport-security\b|\bstp\b|\btrunk\b"
        r"|\bport-channel\b|\blacp\b|\benable\s+stpd\b",
        re.I,
    ),
    DeviceClass.FIREWALL: re.compile(
        r"\bfirewall\b|\bpolicy\b|\brule\b|\bzone\b|\bnameif\b|\bacl\b|\baccess-list\b"
        r"|\biptables\b|\butm\b|\bips\b|\bnat\b",
        re.I,
    ),
}

# Filename hints. Consulted only when no defining construct matched, but BEFORE
# the vendor prior — because vendors such as D-Link, NETGEAR, TP-Link, Ubiquiti
# and Ruijie ship both switches and access points, so the vendor alone cannot
# distinguish their product lines while the filename usually can.
FILENAME_CLASS_HINTS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"(?:^|[_\-.])(?:wf|ap|wifi|wlan|wlc)(?:$|[_\-.])|_wifi|wifi_", re.I), DeviceClass.WIRELESS_AP),
    (re.compile(r"(?:^|[_\-.])(?:sw|switch)(?:$|[_\-.])|_sw[_\-.]|switch", re.I), DeviceClass.NETWORK_SWITCH),
    (re.compile(r"(?:^|[_\-.])(?:fw|firewall|ngfw|utm)(?:$|[_\-.])|firewall", re.I), DeviceClass.FIREWALL),
    (re.compile(r"(?:^|[_\-.])(?:rt|rtr|router)(?:$|[_\-.])|router", re.I), DeviceClass.ROUTER),
    (re.compile(r"(?:^|[_\-.])(?:lb|f5|bigip)(?:$|[_\-.])", re.I), DeviceClass.LOAD_BALANCER),
    (re.compile(r"(?:^|[_\-.])(?:plc|scada|hmi|rtu)(?:$|[_\-.])", re.I), DeviceClass.IOT_CONTROLLER),
    (re.compile(r"(?:^|[_\-.])(?:cam|ipcam|camera|sensor)(?:$|[_\-.])", re.I), DeviceClass.IOT_ENDPOINT),
    # Deliberately excludes a bare "iot" token: it establishes the asset group
    # but not the subclass, and letting it imply "gateway" mislabelled every
    # PLC and camera whose filename merely began with "IOT-".
    (re.compile(r"(?:^|[_\-.])(?:gw|gateway|modem|cellular)(?:$|[_\-.])", re.I), DeviceClass.IOT_GATEWAY),
]


# Vendor-family prior used only to break a tie, never to override evidence.
VENDOR_CLASS_PRIOR: Dict[str, Tuple[str, float]] = {
    "fortinet_fortios": (DeviceClass.FIREWALL, 2.0),
    "palo_alto_panos": (DeviceClass.FIREWALL, 2.5),
    "cisco_asa": (DeviceClass.FIREWALL, 2.5),
    "cisco_firepower": (DeviceClass.FIREWALL, 2.5),
    "checkpoint_gaia": (DeviceClass.FIREWALL, 2.5),
    "sophos_xg": (DeviceClass.FIREWALL, 2.5),
    "pfsense": (DeviceClass.FIREWALL, 2.5),
    "opnsense": (DeviceClass.FIREWALL, 2.5),
    "forcepoint": (DeviceClass.FIREWALL, 2.5),
    "watchguard": (DeviceClass.FIREWALL, 2.5),
    "sonicwall": (DeviceClass.FIREWALL, 2.5),
    "barracuda": (DeviceClass.FIREWALL, 2.5),
    "hillstone": (DeviceClass.FIREWALL, 2.5),
    "sangfor": (DeviceClass.FIREWALL, 2.5),
    "kerio": (DeviceClass.FIREWALL, 2.5),
    "iptables": (DeviceClass.FIREWALL, 2.0),
    "cisco_nxos": (DeviceClass.NETWORK_SWITCH, 2.0),
    "arista_eos": (DeviceClass.NETWORK_SWITCH, 2.0),
    "aruba_aoscx": (DeviceClass.NETWORK_SWITCH, 2.0),
    "aruba_aoss": (DeviceClass.NETWORK_SWITCH, 2.0),
    "extreme_exos": (DeviceClass.NETWORK_SWITCH, 2.0),
    "dell_os10": (DeviceClass.NETWORK_SWITCH, 2.0),
    "sonic": (DeviceClass.NETWORK_SWITCH, 2.0),
    "dlink": (DeviceClass.NETWORK_SWITCH, 1.5),
    "netgear": (DeviceClass.NETWORK_SWITCH, 1.5),
    "brocade_fastiron": (DeviceClass.NETWORK_SWITCH, 1.5),
    "ruckus_icx": (DeviceClass.NETWORK_SWITCH, 1.5),
    "h3c_comware": (DeviceClass.NETWORK_SWITCH, 1.0),
    "ruijie_rgos": (DeviceClass.NETWORK_SWITCH, 1.0),
    "allied_telesis": (DeviceClass.NETWORK_SWITCH, 1.0),
    "cisco_iosxr": (DeviceClass.ROUTER, 2.5),
    "nokia_sros": (DeviceClass.ROUTER, 2.5),
    "vyos": (DeviceClass.ROUTER, 2.0),
    "ubiquiti_edgeos": (DeviceClass.ROUTER, 2.0),
    "mikrotik_routeros": (DeviceClass.ROUTER, 1.5),
    "huawei_vrp": (DeviceClass.ROUTER, 1.0),
    "cisco_ios": (DeviceClass.ROUTER, 0.5),
    "juniper_junos": (DeviceClass.ROUTER, 0.5),
    "f5_tmos": (DeviceClass.LOAD_BALANCER, 2.5),
    "ruckus_smartzone": (DeviceClass.WIRELESS_CONTROLLER, 2.0),
    "mist": (DeviceClass.WIRELESS_AP, 2.5),
    "cambium": (DeviceClass.WIRELESS_AP, 2.5),
    "grandstream": (DeviceClass.WIRELESS_AP, 2.5),
    "engenius": (DeviceClass.WIRELESS_AP, 2.5),
    "openwrt": (DeviceClass.IOT_GATEWAY, 2.0),
    "teltonika": (DeviceClass.IOT_GATEWAY, 2.5),
    "quectel": (DeviceClass.IOT_GATEWAY, 2.5),
    "moxa": (DeviceClass.IOT_GATEWAY, 2.5),
    "advantech": (DeviceClass.IOT_GATEWAY, 2.5),
    "siemens": (DeviceClass.IOT_CONTROLLER, 3.0),
    "schneider": (DeviceClass.IOT_CONTROLLER, 3.0),
    "rockwell": (DeviceClass.IOT_CONTROLLER, 3.0),
    "mitsubishi": (DeviceClass.IOT_CONTROLLER, 3.0),
    "omron": (DeviceClass.IOT_CONTROLLER, 3.0),
    "beckhoff": (DeviceClass.IOT_CONTROLLER, 3.0),
    "wago": (DeviceClass.IOT_CONTROLLER, 3.0),
    "phoenix_contact": (DeviceClass.IOT_CONTROLLER, 3.0),
    "abb": (DeviceClass.IOT_CONTROLLER, 3.0),
    "emerson": (DeviceClass.IOT_CONTROLLER, 3.0),
    "ge_vernova": (DeviceClass.IOT_CONTROLLER, 3.0),
    "honeywell": (DeviceClass.IOT_CONTROLLER, 3.0),
    "johnson_controls": (DeviceClass.IOT_CONTROLLER, 3.0),
    "axis": (DeviceClass.IOT_ENDPOINT, 3.0),
    "hikvision": (DeviceClass.IOT_ENDPOINT, 3.0),
    "dahua": (DeviceClass.IOT_ENDPOINT, 3.0),
    "hanwha": (DeviceClass.IOT_ENDPOINT, 3.0),
    "tasmota": (DeviceClass.IOT_ENDPOINT, 3.0),
    "espressif": (DeviceClass.IOT_ENDPOINT, 3.0),
    "particle": (DeviceClass.IOT_ENDPOINT, 3.0),
    "shelly": (DeviceClass.IOT_ENDPOINT, 3.0),
    "iot_embedded": (DeviceClass.IOT_ENDPOINT, 1.5),
}

# Platform / OS label per vendor family (Level 1).
PLATFORM_BY_VENDOR: Dict[str, str] = {
    "cisco_ios": "Cisco IOS / IOS-XE",
    "cisco_nxos": "Cisco NX-OS",
    "cisco_iosxr": "Cisco IOS-XR",
    "cisco_asa": "Cisco ASA OS",
    "cisco_firepower": "Cisco FTD",
    "juniper_junos": "Juniper Junos",
    "palo_alto_panos": "PAN-OS",
    "fortinet_fortios": "FortiOS",
    "arista_eos": "Arista EOS",
    "aruba_aoscx": "Aruba AOS-CX",
    "aruba_aoss": "Aruba AOS-S",
    "extreme_exos": "ExtremeXOS",
    "dell_os10": "Dell SmartFabric OS10",
    "sonic": "SONiC",
    "huawei_vrp": "Huawei VRP",
    "mikrotik_routeros": "MikroTik RouterOS",
    "vyos": "VyOS",
    "nokia_sros": "Nokia SR OS",
    "h3c_comware": "H3C Comware",
    "openwrt": "OpenWrt",
    "f5_tmos": "F5 TMOS",
    # Firewalls / NGFW
    "checkpoint_gaia": "Check Point Gaia",
    "sophos_xg": "Sophos XG (SFOS)",
    "pfsense": "pfSense",
    "opnsense": "OPNsense",
    "forcepoint": "Forcepoint NGFW",
    "watchguard": "WatchGuard Fireware",
    "sonicwall": "SonicOS",
    "barracuda": "Barracuda CloudGen",
    "hillstone": "Hillstone StoneOS",
    "sangfor": "Sangfor NGAF",
    "kerio": "Kerio Control",
    "iptables": "Linux netfilter",
    # Switching / routing
    "brocade_fastiron": "Brocade FastIron",
    "ruckus_icx": "Ruckus FastIron",
    "allied_telesis": "AlliedWare Plus",
    "ruijie_rgos": "Ruijie RGOS",
    "dlink": "D-Link DGS firmware",
    "netgear": "NETGEAR ProSAFE",
    "zyxel": "Zyxel ZLD",
    "ubiquiti_edgeos": "Ubiquiti EdgeOS",
    "tplink_omada": "TP-Link Omada",
    # Wireless
    "ubiquiti_unifi": "Ubiquiti UniFi",
    "ruckus_smartzone": "Ruckus SmartZone",
    "mist": "Juniper Mist Cloud",
    "cambium": "Cambium cnMaestro",
    "grandstream": "Grandstream GWN",
    "engenius": "EnGenius Cloud",
    "draytek": "DrayTek VigorAP",
    # Industrial / OT
    "siemens": "Siemens TIA / SIMATIC",
    "schneider": "Schneider EcoStruxure",
    "rockwell": "Rockwell Studio 5000",
    "mitsubishi": "Mitsubishi GX Works",
    "omron": "Omron Sysmac Studio",
    "beckhoff": "Beckhoff TwinCAT",
    "wago": "WAGO e!COCKPIT",
    "phoenix_contact": "Phoenix Contact PLCnext",
    "abb": "ABB Automation Builder",
    "emerson": "Emerson DeltaV",
    "ge_vernova": "GE PACSystems",
    "honeywell": "Tridium Niagara 4",
    "johnson_controls": "Johnson Controls Metasys",
    # Cameras / endpoints / gateways
    "axis": "AXIS OS",
    "hikvision": "Hikvision firmware",
    "dahua": "Dahua firmware",
    "hanwha": "Hanwha Wisenet firmware",
    "tasmota": "Tasmota",
    "espressif": "ESPHome",
    "particle": "Particle Device OS",
    "shelly": "Shelly firmware",
    "teltonika": "Teltonika RutOS",
    "quectel": "Quectel AT firmware",
    "moxa": "Moxa firmware",
    "advantech": "Advantech WISE",
    "iot_embedded": "Embedded Linux / RTOS",
    "cisco_meraki": "Cisco Meraki Dashboard",
    "aruba_instant": "Aruba InstantOS",
    "extreme_wing": "Extreme WiNG",
}


# ---------------------------------------------------------------------------
# Detection helpers
# ---------------------------------------------------------------------------

_HOSTNAME_PATTERNS = (
    re.compile(r"^\s*hostname\s+(\S+)", re.I | re.M),
    re.compile(r"^\s*switchname\s+(\S+)", re.I | re.M),
    re.compile(r"^\s*sysname\s+(\S+)", re.I | re.M),
    re.compile(r"\bset\s+system\s+host-name\s+'?([^\s';]+)", re.I),
    re.compile(r"\bhost-name\s+([^\s;]+)", re.I),
    re.compile(r"\bset\s+hostname\s+(\S+)", re.I),
    re.compile(r"\bset\s+deviceconfig\s+system\s+hostname\s+(\S+)", re.I),
    re.compile(r'"?hostname"?\s*[:=]\s*"?([^",\s]+)', re.I),
    re.compile(r'\bconfigure\s+snmp\s+sysName\s+"([^"]+)"', re.I),
    re.compile(r'\bdevice[._]name\s*[:=]\s*"?([^",\s]+)', re.I),
    re.compile(r'<Device\s+name="([^"]+)"', re.I),
    re.compile(r'<Controller\s+Name="([^"]+)"', re.I),
    re.compile(r'"NAME"\s*:\s*"([^"]+)"', re.I),
    re.compile(r'"name"\s*:\s*"([^"]+)"', re.I),
)

# Role hints from operator naming conventions. Weak on their own.
_ROLE_NAME_HINTS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\b(?:spine)\b", re.I), NetworkRole.DC_SPINE),
    (re.compile(r"\b(?:leaf|tor)\b", re.I), NetworkRole.DC_LEAF),
    (re.compile(r"\b(?:core|cor)\b", re.I), NetworkRole.CORE),
    (re.compile(r"\b(?:dist|distribution|idf|mdf)\b", re.I), NetworkRole.DISTRIBUTION),
    (re.compile(r"\b(?:access|acc|edge-sw)\b", re.I), NetworkRole.ACCESS),
    (re.compile(r"\b(?:wan|mpls)\b", re.I), NetworkRole.WAN),
    (re.compile(r"\b(?:branch|br|site|retail|store)\b", re.I), NetworkRole.BRANCH),
    (re.compile(r"\b(?:perim|perimeter|dmz|internet|inet)\b", re.I), NetworkRole.PERIMETER),
    (re.compile(r"\b(?:edge|pe|ce)\b", re.I), NetworkRole.EDGE),
    (re.compile(r"\b(?:guest|wifi|wlan|ap)\b", re.I), NetworkRole.WIRELESS_ACCESS),
]


def extract_hostname(raw: str) -> Optional[str]:
    for pattern in _HOSTNAME_PATTERNS:
        match = pattern.search(raw)
        if match:
            value = match.group(1).strip().strip('"\';')
            if value:
                return value
    return None


def detect_capabilities(raw: str) -> List[str]:
    """Every capability the configuration demonstrates, sorted for stability."""
    return sorted(
        name for name, pattern in CAPABILITY_SIGNALS.items() if pattern.search(raw)
    )


def identify_model(raw: str, hostname: Optional[str] = None) -> Optional[ModelRule]:
    """
    Match the configuration against the model registry.

    Searched in order of trustworthiness: an explicit hardware string in the
    config body beats a model embedded in the operator's hostname convention,
    which in turn beats nothing.
    """
    haystacks = [raw[:4000]]
    if hostname:
        haystacks.insert(0, hostname)
    for haystack in haystacks:
        for rule in MODEL_REGISTRY:
            if rule[0].search(haystack):
                return rule
    return None


def _score_class_evidence(raw: str) -> Dict[str, float]:
    """
    Score structural evidence per class, after applying eligibility gates.

    A class whose defining construct is absent scores zero regardless of how
    many incidental signals matched — see CLASS_REQUIRED_SIGNALS.
    """
    scores: Dict[str, float] = {}
    for klass, signals in CLASS_STRUCTURAL_SIGNALS.items():
        gate = CLASS_REQUIRED_SIGNALS.get(klass)
        if gate is not None and not gate.search(raw):
            continue
        total = 0.0
        for pattern, weight in signals:
            if pattern.search(raw):
                total += weight
        if total:
            scores[klass] = total
    return scores


def _model_rule_is_plausible(rule: ModelRule, raw: str) -> bool:
    """
    Sanity-check a model-registry hit against the configuration.

    Model patterns are short (``\\b8325\\b``, ``\\bmx\\s*\\d+\\b``) and can collide
    with unrelated numbers such as a VLAN id, port number or IP octet. Before
    trusting a match, require that the class it implies is at least eligible.
    """
    implied_class = rule[1]
    gate = CLASS_REQUIRED_SIGNALS.get(implied_class)
    if gate is None:
        return True
    return bool(gate.search(raw))


# ---------------------------------------------------------------------------
# Defining constructs — the decision cascade
# ---------------------------------------------------------------------------
# Device classes are not equally-weighted competitors: each has a construct
# without which it simply is not that class. Scoring them against one another
# let incidental mentions win (a switch naming a VLAN "GUEST-WIFI" outscoring a
# real access point). An ordered cascade on defining constructs, most specific
# first, matches how an engineer actually reads a config.
#
# (class, pattern, human-readable basis)
DEFINING_CASCADE: List[Tuple[str, re.Pattern, str]] = [
    (DeviceClass.IOT_CONTROLLER,
     re.compile(r"\bprotectionlevel\b|\bcipsecurity\b|\bslmpsecurity\b|\bsysmacsecurity\b"
                r"|\bdeltavsecurity\b|\bmetasyssecurity\b|\badssecurity\b|\bmarkviepolicy\b"
                r"|\babbconfiguration\b|\bplcconfiguration\b|\brslogix5000project\b"
                r"|\bmelsecconfig\b|\bniagara\b|\bfoxs?service\b|\btcconfig\b"
                r"|\bmodbus\.(?:tcp|write)\b|\bwrite_protect\b|\bsafety_plc\b", re.I),
     "industrial control platform schema"),

    (DeviceClass.IOT_ENDPOINT,
     re.compile(r"\bonvif\b|\bservices\.rtsp\b|\bmqtthost\b|\bwebpassword\b|\bsetoption\d+\b"
                r"|\besphome\b|\bfallback_hotspot\b|\blorawan?\.\w+\b|\bdev_eui\b"
                r"|\bzigbee\.\w+\b|\bstream\.main\b|\btpm_2_0_active\b", re.I),
     "camera / smart-device firmware keys"),

    (DeviceClass.IOT_GATEWAY,
     re.compile(r"\bcgdcont\b|\bqflock\b|\bqsslcfg\b|\buci\s+(?:set|commit)\b"
                r"|\bpackage\s+(?:network|firewall|system)\b|\bnport\b|\bwise-\d+\b"
                r"|\badam-\d+\b|\bmodbus_tcp_firewall\b", re.I),
     "cellular / embedded gateway configuration"),

    (DeviceClass.WIRELESS_CONTROLLER,
     re.compile(r"\bcapwap\b|\bap\s+dot11\s+(?:5ghz|24ghz)\b|\bap-group\b|\bap\s+name\b"
                r"|\brogue\s+ap\b|\bzonedirector\b|\bsmartzone\b|\bwireless\s+security\s+dot11w\b",
                re.I),
     "wireless controller / AP management plane"),

    (DeviceClass.WIRELESS_AP,
     re.compile(r"\bdot11radio\b|\b802\.11[abgnacax]{1,3}\b|\bradio\s*(?:profile|\d\b|2\.4|5g)"
                r"|\bradio\.\d\b|\bradio_table\b|\bieee_mode\b|/interface\s+wireless"
                r"|\bcaps-man\b|\bchannel[-_\s]?width\b|\btx[-_\s]?power\b"
                r"|\bband[-_\s]?steering\b|\bwireless\.\d?\.?ssid\b|\bwlanconf\b"
                r"|\bwireless\.ssid\d*\b|\bssid_broadcast\b|\bintra_bss\b|\bhide_ssid\b"
                # SMB access points express radios as "set wireless ssid N ..."
                # or a wireless_networks array rather than a dot11 stanza.
                r"|\bset\s+wireless\b|\bwireless\s+ssid\b|\bwireless_networks\b"
                r"|\bwlan\s+ssid\b|\bssid\s+\d+\s+\"|\bwifi[-_]?iface\b"
                r"|\bclient[-_]?isolation\b|\bwireless\s+auth\b"
                # Vendor-integrated AP provisioning: a FortiAP is configured
                # through FortiOS and an Aruba Instant AP through its own wlan
                # profiles, so neither shows a classic dot11 radio stanza. Without
                # these, both fell through to their vendor's firewall/switch prior.
                r"|\bconfig\s+wireless-controller\b|\bwtp-profile\b|\bintra-vap-privacy\b"
                r"|\bwlan\s+ssid-profile\b|\bopmode\s+wpa\b|\bmfp-mandatory\b|\brf-band\b"
                r"|\bencryption-type\s+ccmp\b|\bauthentication-type\s+wpa\b"
                r"|\bprotected-mgmt-frame\b|\bvap-profile\s+name\b|\bssid-profile\s+name\b",
                re.I),
     "radio-layer configuration"),

    (DeviceClass.LOAD_BALANCER,
     re.compile(r"\bltm\s+(?:virtual|pool|node)\b|\bsnat\s+(?:automap|pool)\b"
                r"|\bpersistence\s+(?:profile|cookie|source-addr)\b|\bhaproxy\b"
                r"|\bupstream\s+\S+\s*\{|\bpool\s+members?\b|\bbig-?ip\b", re.I),
     "load-balancing virtual server / pool constructs"),

    (DeviceClass.FIREWALL,
     re.compile(r"\bconfig\s+firewall\s+policy\b|\bset\s+rulebase\s+security\s+rules\b"
                r"|\bset\s+security\s+(?:policies|zones)\b|\bnameif\b|\bsecurity-level\b"
                r"|\bfrom-zone\b|\bzone-pair\b|\bsecurity-zone\b|\bsource_zone\b"
                r"|\bfirewall-rule\b|\bpolicy-type\s+firebox\b|\butm-status\b"
                r"|\bips-sensor\b|\bav-profile\b|\bwebfilter\b|\bweb-filter\b"
                r"|\biptables\b|\bnftables\b|\bset\s+firewall-rule\b"
                r"|\bsystem\s+management\s+lockout\b|\baccess-group\s+\S+\s+in\s+interface\b",
                re.I),
     "stateful security policy / zone model"),
]

# Layer-2 forwarding constructs. Presence of ANY of these makes the hardware a
# switch, however much routing it also performs — this is the rule that stops
# "router bgp" from turning an L3 switch into a router.
_L2_FORWARDING = re.compile(
    r"\bswitchport\b|\bmac\s*-?\s*address-table\b|\bspanning-tree\b|\benable\s+stpd\b"
    r"|\bfamily\s+ethernet-switching\b|\bvlan\s+(?:access|trunk|batch)\b"
    r"|\bconfigure\s+vlan\s+\S+\s+add\s+ports\b|\bport-security\b|\bstorm-control\b"
    r"|\bdhcp\s+snooping\b|\bswitchport\s+mode\b|\bvlan\s+database\b",
    re.I,
)

# Constructs that indicate a routed WAN/provider edge rather than a bridged LAN.
_ROUTED_ONLY = re.compile(
    r"\bencapsulation\s+(?:ppp|hdlc|frame-relay)\b|\binterface\s+(?:serial|atm|pos|dialer|cellular)\b"
    r"|\baddress-family\s+vpnv4\b|\bmpls\s+ldp\s+router-id\b|\bip\s+vrf\s+forwarding\b"
    r"|\binterface\s+tengige\d+/\d+/\d+/\d+\b|\binterface\s+ge-\d+/\d+/\d+\b"
    r"|\brouting-instances\b|\bip\s+route-static\b|/ip\s+route\s+add|\bset\s+protocols\s+static\b",
    re.I,
)


def _classify_by_cascade(
    raw: str, caps: set, vendor: Optional[str], filename: Optional[str] = None
) -> Tuple[str, float, str, bool, Optional[str]]:
    """
    Resolve device class by defining construct, most specific first.

    Returns (device_class, confidence, basis, ambiguity, ambiguity_reason).
    """
    for klass, pattern, description in DEFINING_CASCADE:
        if pattern.search(raw):
            return klass, 0.88, f"defining construct: {description}", False, None

    # Remaining case is the genuinely overlapping pair: switch vs router.
    has_l2 = bool(_L2_FORWARDING.search(raw))
    has_routed_wan = bool(_ROUTED_ONLY.search(raw))
    routes = bool(caps & _L3_CAPABILITIES)

    if has_l2:
        # L2 forwarding present. This is switch hardware even when it also runs
        # BGP/OSPF — the routing shows up in capabilities and network_role.
        note = "layer-2 forwarding constructs present"
        if routes:
            note += " alongside routing protocols (L3 switch)"
        return DeviceClass.NETWORK_SWITCH, 0.86, f"defining construct: {note}", False, None

    if has_routed_wan or routes:
        return (
            DeviceClass.ROUTER,
            0.82,
            "defining construct: routed interfaces with no layer-2 bridging",
            False,
            None,
        )

    # Filename before vendor: a vendor that ships both switches and APs cannot
    # be disambiguated by vendor alone, but "..._wifi_ap.conf" can.
    if filename:
        for pattern, klass in FILENAME_CLASS_HINTS:
            if pattern.search(filename):
                return klass, 0.60, f"filename convention ({filename})", False, None

    prior = VENDOR_CLASS_PRIOR.get(str(vendor or "").lower())
    if prior:
        return prior[0], 0.55, f"vendor product-line prior ({vendor})", False, None

    return (
        DeviceClass.UNKNOWN,
        0.0,
        "no defining construct found",
        True,
        "Configuration contains no forwarding, policy, radio or control-protocol "
        "construct that identifies a hardware class. Too sparse to classify.",
    )


def infer_network_role(
    device_class: str,
    capabilities: List[str],
    raw: str,
    hostname: Optional[str],
    model_role: Optional[str],
) -> Tuple[str, float, List[str]]:
    """
    Infer deployment role from capabilities and topology shape.

    Role is genuinely soft information — two identically configured switches can
    occupy different roles — so this returns a confidence alongside the label and
    never claims certainty.
    """
    caps = set(capabilities)
    reasons: List[str] = []
    candidate = model_role or NetworkRole.UNKNOWN
    confidence = 0.55 if model_role else 0.0
    if model_role:
        reasons.append(f"model registry suggests {model_role}")

    # Data-centre fabric is the most distinctive shape.
    if "VXLAN_EVPN" in caps:
        spine = bool(re.search(r"\bspine\b", f"{hostname or ''} {raw[:2000]}", re.I))
        candidate = NetworkRole.DC_SPINE if spine else NetworkRole.DC_LEAF
        confidence = 0.80
        reasons.append("VXLAN/EVPN fabric detected")
    # Perimeter vs internal segmentation for policy devices.
    elif device_class in (DeviceClass.FIREWALL, DeviceClass.SECURITY_APPLIANCE):
        if "NAT" in caps or re.search(r"\b(?:outside|untrust|wan)\b", raw, re.I):
            candidate, confidence = NetworkRole.PERIMETER, 0.75
            reasons.append("external zone plus NAT indicates perimeter placement")
        else:
            candidate, confidence = NetworkRole.SEGMENTATION, 0.60
            reasons.append("policy enforcement without an external zone")
    elif device_class in (DeviceClass.WIRELESS_AP, DeviceClass.WIRELESS_CONTROLLER):
        candidate, confidence = NetworkRole.WIRELESS_ACCESS, 0.85
        reasons.append("wireless service delivery")
    elif device_class == DeviceClass.IOT_CONTROLLER:
        if {"BACNET"} & caps:
            candidate, confidence = NetworkRole.BUILDING_AUTOMATION, 0.80
            reasons.append("BACnet building-automation stack")
        else:
            candidate, confidence = NetworkRole.OT_CELL, 0.75
            reasons.append("industrial control protocols")
    elif device_class in (DeviceClass.IOT_GATEWAY, DeviceClass.IOT_ENDPOINT):
        candidate, confidence = NetworkRole.IOT_EDGE, 0.75
        reasons.append("IoT edge device")
    else:
        # Routers and switches: distinguish by routing scope and port density.
        access_ports = len(re.findall(r"\bswitchport\s+mode\s+access\b", raw, re.I))
        has_ebgp = bool(re.search(r"\bremote-as\b|\bpeer-as\b|\bexternal\b", raw, re.I))
        igp = bool(caps & {"OSPF", "ISIS"})

        if "MPLS" in caps or ("BGP" in caps and igp):
            candidate, confidence = NetworkRole.CORE, 0.75
            reasons.append("MPLS or BGP+IGP indicates core/provider placement")
        elif "BGP" in caps and has_ebgp and "NAT" in caps:
            candidate, confidence = NetworkRole.INTERNET_GATEWAY, 0.70
            reasons.append("eBGP with NAT indicates an internet edge")
        elif "BGP" in caps and has_ebgp:
            candidate, confidence = NetworkRole.EDGE, 0.68
            reasons.append("eBGP peering indicates edge placement")
        elif access_ports >= 8 or "PORT_SECURITY" in caps:
            candidate, confidence = NetworkRole.ACCESS, 0.72
            reasons.append(f"{access_ports} access ports / port-security present")
        elif igp and caps & _L2_CAPABILITIES:
            candidate, confidence = NetworkRole.DISTRIBUTION, 0.65
            reasons.append("IGP plus L2 bridging indicates distribution layer")
        elif "CELLULAR_WAN" in caps or "IPSEC_VPN" in caps:
            candidate, confidence = NetworkRole.BRANCH, 0.65
            reasons.append("cellular/IPsec WAN indicates branch placement")
        elif "STATIC_ROUTING" in caps and "NAT" in caps:
            candidate, confidence = NetworkRole.INTERNET_GATEWAY, 0.62
            reasons.append("default route with NAT indicates an internet gateway")

    # Operator naming convention can lift confidence but not invent a role.
    if hostname:
        for pattern, role in _ROLE_NAME_HINTS:
            if pattern.search(hostname):
                if role == candidate:
                    confidence = min(0.95, confidence + 0.12)
                    reasons.append(f"hostname corroborates {role}")
                elif candidate == NetworkRole.UNKNOWN:
                    candidate, confidence = role, 0.50
                    reasons.append(f"hostname convention suggests {role}")
                break

    return candidate, round(confidence, 2), reasons


def build_device_profile(
    raw_text: str,
    filename: Optional[str] = None,
    vendor: Optional[str] = None,
    vendor_confidence: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Produce the full layered profile for one configuration.

    Determination order for ``device_class``:
      1. model registry match  (authoritative — the hardware is named)
      2. structural evidence   (forwarding/policy constructs, never protocols)
      3. vendor product prior  (tie-break only)
      4. UNKNOWN + ambiguity flag
    """
    raw = raw_text or ""
    hostname = extract_hostname(raw)
    capabilities = detect_capabilities(raw)
    caps = set(capabilities)

    # Vendor-layer certainty, reported separately from the device-class decision
    # and separately again from any human-escalation requirement.
    try:
        from tools.fingerprint import fingerprint_vendor_ex
        vendor_result = fingerprint_vendor_ex(raw)
        vendor_status = vendor_result["classification_status"]
        vendor_status_reason = vendor_result["status_reason"]
        vendor_runner_up = vendor_result["runner_up"]
    except Exception:
        vendor_status, vendor_status_reason, vendor_runner_up = "UNSPECIFIED", None, []

    platform = PLATFORM_BY_VENDOR.get(str(vendor or "").lower())
    model_rule = identify_model(raw, hostname)

    model_label: Optional[str] = None
    model_role: Optional[str] = None
    device_class = DeviceClass.UNKNOWN
    class_confidence = 0.0
    basis = "none"
    ambiguity = False
    ambiguity_reason: Optional[str] = None

    if model_rule is not None and not _model_rule_is_plausible(model_rule, raw):
        # A short model pattern matched a number that was not a model. Fall
        # through to structural evidence rather than trusting a spurious hit.
        model_rule = None

    if model_rule is not None:
        _, model_class, model_role, _l3, model_label = model_rule
        device_class = model_class
        class_confidence = 0.93
        basis = f"model registry ({model_label})"
    else:
        device_class, class_confidence, basis, ambiguity, ambiguity_reason = (
            _classify_by_cascade(raw, caps, vendor, filename)
        )

    network_role, role_confidence, role_reasons = infer_network_role(
        device_class, capabilities, raw, hostname, model_role
    )

    l3_capable = bool(caps & _L3_CAPABILITIES)
    l2_capable = bool(caps & _L2_CAPABILITIES)
    routing_protocols = sorted(caps & {"BGP", "OSPF", "ISIS", "EIGRP", "RIP", "MPLS"})

    group = DEVICE_CLASS_TO_GROUP.get(device_class, AssetGroup.UNKNOWN)

    return {
        # Level 1 — product identity
        "vendor": vendor,
        "platform": platform,
        "model": model_label,
        # Level 2 — device class
        "device_class": device_class,
        "device_class_display": DEVICE_CLASS_DISPLAY.get(device_class, device_class),
        "device_class_icon": DEVICE_CLASS_ICON.get(device_class, "\u2753"),
        "device_class_confidence": class_confidence,
        "device_class_basis": basis,
        # Level 3 — operational role
        "network_role": network_role,
        "network_role_display": NETWORK_ROLE_DISPLAY.get(network_role, network_role),
        "network_role_confidence": role_confidence,
        "network_role_reasons": role_reasons,
        # Capabilities
        "capabilities": capabilities,
        "routing_protocols": routing_protocols,
        "routing_capable": l3_capable,
        "l3_capable": l3_capable,
        "l2_capable": l2_capable,
        # Honest uncertainty. `classification_status` describes how well the
        # asset was IDENTIFIED. It is deliberately not wired to human escalation:
        # `human_required` is decided by unmapped commands during the audit, not
        # by how confidently we recognised the hardware.
        "ambiguity": ambiguity,
        "ambiguity_reason": ambiguity_reason,
        "classification_status": vendor_status,
        "classification_status_reason": vendor_status_reason,
        "vendor_runner_up": vendor_runner_up,
        "human_required": False,
        # Coarse grouping for the Devices-page badge
        "asset_group": group,
        "asset_group_display": ASSET_GROUP_DISPLAY.get(group, "Unclassified Config"),
        "hostname": hostname,
    }


def summarize_profiles(devices: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate an inventory by device class and by network role."""
    by_class: Dict[str, Dict[str, Any]] = {}
    by_role: Dict[str, int] = {}
    capability_counts: Dict[str, int] = {}
    ambiguous = 0

    for dev in devices:
        # Prefer `hardware_class`: in API payloads the compatibility shim
        # overwrites `device_class` with the coarse asset group, so reading it
        # here would bucket everything as "network"/"security"/"iot".
        klass = dev.get("hardware_class") or dev.get("device_class") or DeviceClass.UNKNOWN
        entry = by_class.setdefault(klass, {
            "device_class": klass,
            "device_class_display": DEVICE_CLASS_DISPLAY.get(klass, klass),
            "device_class_icon": DEVICE_CLASS_ICON.get(klass, "\u2753"),
            "asset_group": DEVICE_CLASS_TO_GROUP.get(klass, AssetGroup.UNKNOWN),
            "count": 0,
            "filenames": [],
        })
        entry["count"] += 1
        entry["filenames"].append(dev.get("filename"))

        role = dev.get("network_role") or NetworkRole.UNKNOWN
        by_role[role] = by_role.get(role, 0) + 1
        for cap in dev.get("capabilities") or []:
            capability_counts[cap] = capability_counts.get(cap, 0) + 1
        if dev.get("ambiguity"):
            ambiguous += 1

    return {
        "by_device_class": sorted(by_class.values(), key=lambda e: -e["count"]),
        "by_network_role": dict(sorted(by_role.items(), key=lambda kv: -kv[1])),
        "top_capabilities": dict(sorted(capability_counts.items(), key=lambda kv: -kv[1])[:15]),
        "ambiguous_count": ambiguous,
        "total": len(devices),
    }

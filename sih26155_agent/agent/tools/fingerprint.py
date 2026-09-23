"""Tool 2 — Vendor Fingerprinting. Rule-based weighted signature matching.

Per the ML training plan: this ships day one with zero training data. A
trained text classifier only becomes worthwhile once 200-500 labeled config
files per vendor exist.

v2 changes over the original flat marker list:
  * Markers are split into ``strong`` (highly distinctive) and ``weak``
    (supporting) tiers so a single decisive line outranks several generic ones.
  * ``exclude`` markers disambiguate overlapping grammars. The original
    implementation misfiled VyOS configs as Juniper because both use
    ``set system ...``; VyOS-specific stanzas now veto the Juniper match.
  * Confidence is damped when the runner-up vendor scores close to the winner,
    so ambiguous configs report low confidence instead of false precision.
  * Proper display names replace ``value.replace("_", " ").title()``, which
    produced strings like "Cisco Asa" and "Fortinet Fortios".
"""

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path as _Path
from typing import Dict, Tuple

_PROJECT_ROOT = _Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(_PROJECT_ROOT / "agent"))
from security_baseline_schema import VendorFamily  # noqa: E402

STRONG_WEIGHT = 3.0
WEAK_WEIGHT = 1.0
STRUCTURAL_WEIGHT = 2.0
CONTRADICTION_PENALTY = 0.20

# Confidence thresholds separating the result states below.
CONFIDENT_SCORE = 0.62
CONFIDENT_MARGIN = 0.15
SPARSE_CONFIG_LINES = 6

# Below this score the evidence is so thin that naming a vendor is a coin flip
# dressed as an answer. Abstaining is the correct output: a truncated config
# whose single matching token happened to belong to Palo Alto is not a Palo Alto
# device, and emitting one converts a harmless refusal into a confident error.
#
# Chosen empirically by sweeping the floor across all 5,000 corpus samples. The
# curve has a distinct knee here:
#
#   floor   correct   wrong   abstain
#   0.00      4865      31       104
#   0.06      4815      21       164
#   0.08      4795      10       195     <- knee: minimum wrong, coverage intact
#   0.12      4775      10       215        (20 correct lost for no gain)
#   0.20      4447       0       553        (348 correct lost to remove 10 errors)
#
# 0.08 reaches the lowest achievable wrong-count without paying for it in
# coverage. Pushing to 0.20 would zero the errors but discard 348 correct
# identifications, which is the wrong trade for an auditing tool.
MIN_EVIDENCE_SCORE = 0.08


class ClassificationStatus:
    """
    Explicit result taxonomy.

    "Unknown because the evidence was insufficient" is not the same outcome as
    "classified incorrectly", and collapsing both into UNKNOWN made the metrics
    unreadable. These states are about *classification certainty* only — they are
    deliberately separate from the human-escalation decision, which is driven by
    unmapped commands at audit time, not by fingerprint confidence.
    """

    CONFIDENT = "CONFIDENT"                          # clear winner, strong evidence
    LOW_EVIDENCE = "LOW_EVIDENCE"                    # a best guess, thin support
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"    # two vendors score alike
    UNKNOWN_EDGE_CASE = "UNKNOWN_EDGE_CASE"          # too sparse to say anything


@dataclass(frozen=True)
class VendorSignature:
    vendor: VendorFamily
    strong: Tuple[str, ...] = ()
    weak: Tuple[str, ...] = ()
    # Hard veto: presence makes this vendor impossible.
    exclude: Tuple[str, ...] = field(default=())
    # Graduated penalty: evidence that argues AGAINST this vendor without ruling
    # it out. A vendor-specific marker should not only raise its own score, it
    # should lower competing hypotheses when the two are mutually exclusive.
    contradicts: Tuple[str, ...] = field(default=())
    # Co-occurrence groups. Every marker in a group must be present for the group
    # to score. This is what distinguishes real structural evidence from a lucky
    # single-token hit, e.g. "/caps-man" + "configuration" together.
    structural: Tuple[Tuple[str, ...], ...] = field(default=())


SIGNATURES = (
    # ---- Cisco ---------------------------------------------------------
    VendorSignature(
        VendorFamily.CISCO_IOS,
        strong=("building configuration", "ip ssh version", "line vty", "service password-encryption"),
        weak=("no ip http server", "logging buffered", "snmp-server community", "exec-timeout", "enable secret"),
        exclude=("feature nxos", "install add file bootflash", "asa version", "! device: arista"),
    ),
    VendorSignature(
        VendorFamily.CISCO_NXOS,
        strong=("feature nxos", "feature bgp", "feature interface-vlan", "nxos.", "feature lacp"),
        weak=("vdc ", "switchname", "feature ssh", "system jumbomtu"),
    ),
    VendorSignature(
        VendorFamily.CISCO_IOSXR,
        strong=("commit", "rp/0/rp0/cpu0", "interface mgmteth0/rp0/cpu0/0", "group root-lr"),
        weak=("configure", "show configuration commit list", "tengige0/", "domain name"),
        exclude=("building configuration", "switchport"),
    ),
    VendorSignature(
        VendorFamily.CISCO_ASA,
        strong=("asa version", "nameif", "security-level", "access-group", "same-security-traffic"),
        weak=("object network", "object-group service", "class-map inspection_default", "anyconnect"),
    ),
    VendorSignature(
        VendorFamily.CISCO_FIREPOWER,
        strong=("firepower", "ftd ", "access-control-policy", "intrusion-policy"),
        weak=("snort", "prefilter-policy", "security-zone"),
    ),
    # ---- Juniper / VyOS (overlapping "set ..." grammar) -----------------
    # Junos ships in two syntaxes and both appear in the wild:
    #   flat  "set system services ssh protocol-version v2"
    #   tree  "system { services { ssh { protocol-version v2; } } }"
    # The original signature only covered the flat form, so every native
    # `show configuration` dump (the hierarchical form) fell through to UNKNOWN.
    VendorSignature(
        VendorFamily.JUNIPER_JUNOS,
        strong=(
            "set security policies", "set firewall filter", "set system login retry-options",
            "delete system services", "set routing-options", "family ethernet-switching",
            "root-authentication", "class super-user", "routing-instances",
            "protocol-version v2;", "instance-type virtual-router",
        ),
        weak=(
            "set system services ssh", "set snmp", "set system syslog",
            "set interfaces ge-", "set vlans",
            "host-name", "encrypted-password", "system {", "interfaces {",
            "security {", "snmp {", "apply-groups",
        ),
        exclude=("set firewall ipv4 name", "set interfaces ethernet eth", "vyos",
                 "disable-password-authentication"),
    ),
    # EdgeOS is a VyOS fork, so their grammars are nearly identical. Without the
    # veto, every EdgeRouter config scored as VyOS.
    VendorSignature(
        VendorFamily.VYOS,
        strong=("vyos", "set firewall ipv4 name", "set interfaces ethernet eth", "disable-password-authentication"),
        weak=("set service ssh", "set protocols static route", "set system host-name", "set system name-server"),
        exclude=("edgeos", "edgerouter", "ubnt", "ubiquiti"),
    ),
    # ---- Firewalls -----------------------------------------------------
    VendorSignature(
        VendorFamily.FORTINET_FORTIOS,
        strong=("config system global", "config firewall policy", "set admin-sport",
                "config system admin",
                # FortiAP access points are provisioned through FortiOS itself
                "config wireless-controller", "wtp-profile", "intra-vap-privacy"),
        weak=("set admin-lockout-threshold", "set srcintf", "set dstintf", "next", "edit ",
              "fortiap", "fortigate"),
    ),
    # SRX and PAN-OS both express "permit traffic from the trust zone to the
    # untrust zone", so zone vocabulary alone cannot separate them. PAN-OS is
    # claimed on its own structural forms, and Junos constructs actively argue
    # against it rather than merely failing to support it.
    VendorSignature(
        VendorFamily.PALO_ALTO_PANOS,
        strong=("set deviceconfig", "set rulebase security rules", "pan-os",
                "set deviceconfig system", "set mgt-config"),
        weak=("service application-default", "set network virtual-router",
              "set profiles ", "set shared ", "set zone "),
        structural=(
            ("set rulebase", "action allow"),
            ("set deviceconfig", "set network"),
            ("set zone", "network layer3"),
        ),
        contradicts=("set system services", "delete system services",
                     "set security policies", "set system host-name",
                     "set system login", "from-zone"),
    ),
    VendorSignature(
        VendorFamily.CHECKPOINT_GAIA,
        strong=("set expert-password", "add rba role", "set clienv", "gaia"),
        weak=("fw policy", "cpstop", "set interface", "add host name"),
    ),
    VendorSignature(
        VendorFamily.SOPHOS_XG,
        strong=("sophos", "system_password", "set service_param", "console_config"),
        weak=("set firewall-rule", "set ips", "set web-filter"),
    ),
    VendorSignature(
        VendorFamily.PFSENSE,
        strong=("pfsense", "<pfsense>", "<filter>", "<rule><type>pass"),
        weak=("<interfaces>", "<dhcpd>", "<nat>", "<system>"),
    ),
    # ---- Switches ------------------------------------------------------
    VendorSignature(
        VendorFamily.ARISTA_EOS,
        strong=("! device: arista", "arista eos", "management api http-commands",
                "eos-", "dcs-7"),
        # The old weak tier ("switchport access vlan", "router bgp", "ip routing",
        # "interface ethernet") is present in essentially every datacentre switch
        # config, so it claimed Cisco Nexus. Arista-specific constructs only.
        weak=("management ssh", "management api", "cipher aes256-ctr",
              "spanning-tree mode mstp"),
        exclude=("feature nxos", "switchname", "building configuration"),
    ),
    VendorSignature(
        VendorFamily.EXTREME_EXOS,
        strong=("configure vlan", "extremexos", "enable sshd2", "configure snmp"),
        weak=("create vlan", "configure ports", "enable lldp"),
    ),
    VendorSignature(
        VendorFamily.DELL_OS10,
        strong=("os10", "dell emc", "dell networking", "interface ethernet1/1/", "system-cli"),
        # "spanning-tree mode" and "snmp-server" appear in every Cisco switch
        # config; as weak markers they pulled Nexus 9300 and Catalyst 9800 here.
        weak=("ip ssh server enable", "smartfabric"),
    ),
    VendorSignature(
        VendorFamily.SONIC,
        strong=("sonic", "config_db.json", "device_metadata", "sonic-cfggen"),
        weak=("portchannel", "bgp_neighbor", "vlan_interface"),
    ),
    VendorSignature(
        VendorFamily.ARUBA_AOSCX,
        # "ssh server vrf" demoted to weak: Cisco IOS-XE uses it too, and as a
        # strong marker it pulled Catalyst 8000 / ISR 4000 configs to Aruba.
        strong=("aoscx", "aruba aoscx", "user admin group administrators",
                "ssh ciphers aes256-ctr", "port-security client-limit"),
        weak=("ssh server vrf", "vlan access", "no telnet server",
              "aaa authentication login default local", "loop-protect"),
    ),
    # ---- Routers / SMB -------------------------------------------------
    VendorSignature(
        VendorFamily.HUAWEI_VRP,
        strong=("stelnet server", "huawei vrp", "local-user", "undo telnet server enable",
                # Huawei AC wireless controllers share the VRP grammar
                "vap-profile name", "ssid-profile name", "security-profile name",
                "sae-password cipher"),
        weak=("sysname", "info-center loghost", "ip route-static", "acl number",
              "service-vlan vlan-id"),
    ),
    # A CAPsMAN-only wireless config contains none of the /system or /ip stanzas
    # that previously defined this signature, so it scored zero for MikroTik and
    # was claimed by generic wireless brands. The /caps-man stanzas are added as
    # first-class evidence, plus co-occurrence groups so a lone token is not
    # enough to claim the vendor.
    VendorSignature(
        VendorFamily.MIKROTIK_ROUTEROS,
        strong=("/system identity", "/ip service", "/ip firewall filter", "routeros",
                "/caps-man", "/interface wireless"),
        weak=("/interface", "/ip address add", "/user set", "/system ntp client",
              "client-to-client-forwarding", "local-forwarding",
              "authentication-types=", "encryption=aes-ccm"),
        structural=(
            ("/caps-man", "configuration add"),
            ("/caps-man", "datapath"),
            ("/caps-man", "security add"),
            ("/ip firewall", "chain="),
            ("/system identity", "set name="),
        ),
    ),
    VendorSignature(
        VendorFamily.UBIQUITI_EDGEOS,
        strong=("edgeos", "edgerouter", "set system login user ubnt"),
        weak=("set service ssh port", "set interfaces ethernet eth", "set firewall name"),
    ),
    VendorSignature(
        VendorFamily.ZYXEL,
        strong=("zyxel", "zynos", "nebula", "nwa1", "usg flex"),
    ),
    # ---- Wireless ------------------------------------------------------
    VendorSignature(
        VendorFamily.UBIQUITI_UNIFI,
        strong=("unifi", "ubnt", "aircontrol", "nanohd"),
        # "ssid", "wpa" and "radio_table" were generic enough that this
        # signature absorbed MikroTik CAPsMAN, Cisco WLC, EnGenius and TP-Link
        # access points. A UniFi claim now needs UniFi evidence.
        weak=("wlanconf", "mgmt.servers", "inform"),
    ),
    VendorSignature(
        VendorFamily.RUCKUS_SMARTZONE,
        strong=("ruckus", "smartzone", "zonedirector", "unleashed"),
    ),
    VendorSignature(
        VendorFamily.TPLINK_OMADA,
        strong=("tp-link", "omada", "eap-controller", "eap245", "eap265", "eap610"),
    ),
    # ---- Load balancer -------------------------------------------------
    VendorSignature(
        VendorFamily.F5_TMOS,
        strong=("ltm virtual", "tmos", "big-ip", "ltm pool"),
        weak=("snat automap", "persistence", "monitor http", "profile clientssl"),
    ),
    # ---- Embedded / IoT ------------------------------------------------
    VendorSignature(
        VendorFamily.OPENWRT,
        strong=("openwrt", "uci set", "config interface 'lan'", "package 'network'"),
        weak=("option proto 'static'", "dropbear", "busybox", "config wifi-iface"),
    ),
    # ---- Additional firewall / NGFW families ---------------------------
    # Markers below were derived from the labelled GAACA corpus rather than
    # guessed: for each vendor group, tokens appearing in >=55% of that
    # vendor's samples and in at most 2 vendor groups overall.
    VendorSignature(
        VendorFamily.FORCEPOINT,
        strong=("forcepoint", "system management lockout enable", "system management session-timeout"),
        weak=("system hostname", "system management ssh", "system management https", "system domain"),
    ),
    VendorSignature(
        VendorFamily.WATCHGUARD,
        strong=("firebox", "policy-type firebox"),
        weak=("admin-lockout attempts", "interface external eth", "trusted eth", "optional eth"),
    ),
    VendorSignature(
        VendorFamily.SONICWALL,
        strong=("sonicos", "sonicwall"),
        weak=("administration", "access-rule", "zone lan", "zone wan"),
    ),
    VendorSignature(
        VendorFamily.BARRACUDA,
        strong=("barracuda", "cloudgen"),
        weak=("firewall rule", "mgmt-access", "box config"),
    ),
    VendorSignature(
        VendorFamily.HILLSTONE,
        strong=("hillstone", "stoneos"),
    ),
    VendorSignature(
        VendorFamily.SANGFOR,
        strong=("sangfor", "ngaf"),
    ),
    VendorSignature(
        VendorFamily.KERIO,
        strong=("kerio", "kerio control"),
        weak=("traffic rule", "interface group"),
    ),
    VendorSignature(
        VendorFamily.OPNSENSE,
        strong=("opnsense", "<opnsense>"),
        weak=("<interfaces>", "<filter>", "<rule>", "<system>"),
    ),
    VendorSignature(
        VendorFamily.IPTABLES,
        strong=("iptables", "-a input", "-a forward", "*filter"),
        weak=("--dport", "-j accept", "-j drop", "-m state"),
    ),

    # ---- Additional routing / switching families ------------------------
    VendorSignature(
        VendorFamily.NOKIA_SROS,
        strong=("nokia", "sr os", "configure system security"),
        weak=("configure system", "configure router", "exit all", "admin save"),
    ),
    # Comware forked from Huawei VRP, so "sysname", "local-user" and
    # "undo telnet" are shared grammar and prove nothing either way. The two are
    # separated on their genuinely divergent constructs: Comware kept Cisco-style
    # "line vty" and adds "password-control", while VRP uses "user-interface vty"
    # and "stelnet server".
    VendorSignature(
        VendorFamily.H3C_COMWARE,
        # "line vty" is Cisco's own construct that Comware merely inherited, so
        # it belongs in the weak tier — as a strong marker it claimed Cisco IOS.
        strong=("h3c", "comware", "password-control"),
        weak=("undo ip http enable", "ssh server enable", "local-user", "line vty"),
        exclude=("stelnet server", "user-interface vty", "vap-profile name"),
    ),
    VendorSignature(
        VendorFamily.BROCADE_FASTIRON,
        strong=("brocade", "fastiron", "netiron", "super-user-password"),
        # "ip access-list" / "aaa authentication" are universal Cisco-style
        # constructs and pulled Catalyst 8000 configs to Brocade.
        weak=("enable super-user-password",),
    ),
    VendorSignature(
        VendorFamily.ALLIED_TELESIS,
        strong=("allied telesis", "awplus", "alliedware"),
        weak=("service password-encryption", "crypto key generate hostkey", "no service telnet"),
    ),
    VendorSignature(
        VendorFamily.RUIJIE_RGOS,
        strong=("ruijie", "rgos", "ssh-server", "wlan-config"),
        weak=("sta-isolation", "enable service ssh-server", "line vty"),
    ),
    VendorSignature(
        VendorFamily.DLINK,
        strong=("d-link", "dgs-", "system_name"),
        weak=("create account admin", "enable ssh", "disable telnet"),
    ),
    VendorSignature(
        VendorFamily.NETGEAR,
        strong=("netgear", "prosafe", "m4300", "m4500"),
        weak=("vlan database", "ip ssh server enable", "no ip telnet server"),
    ),
    VendorSignature(
        VendorFamily.ARUBA_AOSS,
        strong=("aruba-os-switch", "aoss", "password manager"),
        weak=("aaa authentication login privilege-mode", "no telnet-server", "crypto key generate ssh"),
    ),
    VendorSignature(
        VendorFamily.RUCKUS_ICX,
        strong=("ruckus icx", "icx", "fastiron icx"),
        weak=("enable aaa console", "ip ssh", "no telnet server"),
    ),

    # ---- Wireless families ------------------------------------------------
    # Every wireless signature below is brand- or syntax-anchored. Their weak
    # tiers previously held generic tokens ("ssid", "radio", "wireless",
    # "wpa2", "vlan") which appear in EVERY access-point config, so whichever
    # SMB brand happened to sort first absorbed Aruba, Fortinet, Huawei, Meraki
    # and Extreme APs alike. A brand claim now requires brand evidence.
    VendorSignature(
        VendorFamily.ARUBA_INSTANT,
        strong=("wlan ssid-profile", "opmode wpa3-sae-aes", "opmode wpa2-aes",
                "mfp-mandatory", "rf-band", "instant ap"),
        weak=("essid", "wpa-passphrase", "type employee", "type guest",
              "client-isolation", "virtual-controller"),
    ),
    VendorSignature(
        VendorFamily.CISCO_MERAKI,
        strong=("\"ssids\"", "wpaencryptionmode", "enterpriseadminaccess",
                "meraki", "\"authmode\""),
        weak=("\"encryptionmode\"", "8021x-radius", "\"splashpage\"",
              "\"perssidbandwidthlimit\""),
    ),
    VendorSignature(
        VendorFamily.EXTREME_WING,
        strong=("wing", "encryption-type ccmp", "authentication-type wpa3-sae",
                "wpa-wpa2-passphrase", "protected-mgmt-frame"),
        weak=("client-client-communication", "rf-domain", "profile ap",
              "controller-managed"),
    ),
    VendorSignature(
        VendorFamily.MIST,
        strong=("mist", "site_id", "\"wlans\""),
        weak=("gcmp-256", "\"isolation\"", "\"band\""),
    ),
    VendorSignature(
        VendorFamily.CAMBIUM,
        strong=("cambium", "cnpilot", "cnmaestro"),
    ),
    VendorSignature(
        VendorFamily.GRANDSTREAM,
        strong=("grandstream", "gwn76", "gwn source"),
    ),
    VendorSignature(
        VendorFamily.ENGENIUS,
        strong=("engenius", "engenius cloud", "ecw2", "ews3"),
    ),
    VendorSignature(
        VendorFamily.DRAYTEK,
        strong=("draytek", "vigor"),
    ),

    # ---- Industrial control / OT (XML and JSON project formats) ----------
    # "deviceconfiguration" is a generic XML root element, not Siemens evidence:
    # a two-line truncated file containing only `<DeviceConfiguration/>` was
    # enough to name Siemens. Demoted to weak and backed by co-occurrence groups,
    # so the root element only counts alongside a Siemens-specific child.
    VendorSignature(
        VendorFamily.SIEMENS,
        strong=("simatic", "protectionlevel", "securepgpccommunication",
                "putgetcommunication", "webserverprotection"),
        weak=("s7-1500", "s7-1200", "pn/dp", "profinet", "requirehttps",
              "deviceconfiguration"),
        structural=(
            ("deviceconfiguration", "security"),
            ("simatic", "protectionlevel"),
        ),
    ),
    VendorSignature(
        VendorFamily.SCHNEIDER,
        strong=("modicon", "plcconfiguration", "cybersecurityprofile",
                "modbusportfiltering", "disableunusedprotocols"),
        weak=("m580", "m241", "snmpv1v2", "userauthentication"),
    ),
    VendorSignature(
        VendorFamily.ROCKWELL,
        strong=("rslogix5000project", "controllogix", "compactlogix",
                "cipsecurity", "factorytalksecuritypolicy", "ethernetipsecuritymode"),
        weak=("schemaversion", "enforcesecurity", "<controller "),
    ),
    VendorSignature(
        VendorFamily.MITSUBISHI,
        strong=("melsecconfig", "melsec", "slmpsecurity"),
        weak=("iq-r", "iq-f", "ipfilter", "authenticationrequired"),
    ),
    VendorSignature(
        VendorFamily.OMRON,
        strong=("sysmacsecurity", "sysmac", "operationrights"),
        weak=("nj/nx", "packetfilter", "<controller"),
    ),
    VendorSignature(
        VendorFamily.BECKHOFF,
        strong=("beckhoff", "twincat", "tcconfig", "secureads", "adssecurity"),
        weak=("cx5130", "cx9020", "requireauth", "targetnetid"),
    ),
    VendorSignature(
        VendorFamily.WAGO,
        strong=("wago", "pfc200", "modbus_tcp_firewall", "permit_root_login"),
        weak=("codesys", "\"firewall\"", "\"services\""),
    ),
    VendorSignature(
        VendorFamily.PHOENIX_CONTACT,
        strong=("phoenix contact", "plcnext", "axc f", "security_profile", "user_management"),
        weak=("input_policy", "\"firewall\"", "profinet"),
    ),
    VendorSignature(
        VendorFamily.ABB,
        strong=("abbconfiguration", "ac500", "rtu500"),
        weak=("iec60870_5_104", "webaccess", "httpsonly", "securitylevel"),
    ),
    VendorSignature(
        VendorFamily.EMERSON,
        strong=("deltavsecurity", "deltav", "nodelockdown", "smartfirewall"),
        weak=("ovation", "incomingblocked", "<node"),
    ),
    VendorSignature(
        VendorFamily.GE_VERNOVA,
        strong=("markviepolicy", "mark vie", "pacsystems", "dnp3secureauth", "logicprotection"),
        weak=("rx3i", "writelock"),
    ),
    VendorSignature(
        VendorFamily.HONEYWELL,
        strong=("niagara", "foxservice", "foxsservice", "securityservice"),
        weak=("<station", "passwordpolicy", "maxfailedattempts", "minlength"),
    ),
    VendorSignature(
        VendorFamily.JOHNSON_CONTROLS,
        strong=("metasyssecurity", "metasys", "johnson controls"),
        weak=("nae", "sne", "authenticationmode", "<engine"),
    ),

    # ---- IP cameras ------------------------------------------------------
    VendorSignature(
        VendorFamily.AXIS,
        strong=("axis", "\"root\"", "ieee8021x"),
        weak=("\"network\"", "\"properties\"", "serialnumber", "\"rtsp\"", "strictttransportsecurity"),
    ),
    VendorSignature(
        VendorFamily.HIKVISION,
        strong=("hikvision", "securityconfig", "onvifsecurity", "illegalloginlock"),
        weak=("devicename", "ds-2cd", "authtype", "httpsport"),
    ),
    VendorSignature(
        VendorFamily.DAHUA,
        strong=("dahua", "ipc-hfw", "ipc-hdw"),
        weak=("ipfilter", "\"rtsp\"", "\"onvif\""),
    ),
    VendorSignature(
        VendorFamily.HANWHA,
        strong=("hanwha", "wisenet", "tpm_2_0_active", "https_mandatory"),
        weak=("admin_pass", "\"camera\"", "x-series"),
    ),

    # ---- Smart devices / cellular gateways -------------------------------
    VendorSignature(
        VendorFamily.TASMOTA,
        strong=("tasmota", "mqtthost", "webpassword", "setoption"),
        weak=("mqttuser", "mqttport", "mqttpassword", "sonoff"),
    ),
    VendorSignature(
        VendorFamily.ESPRESSIF,
        strong=("esphome", "espressif", "esp32"),
        weak=("\"wifi\"", "\"api\"", "\"ota\"", "fallback_hotspot"),
    ),
    VendorSignature(
        VendorFamily.PARTICLE,
        strong=("particle", "deviceos", "lockprotected"),
        weak=("deviceid", "boron", "photon"),
    ),
    VendorSignature(
        VendorFamily.SHELLY,
        strong=("shelly", "shelly plus", "pro 4pm"),
        weak=("\"mqtt\"", "\"wifi\"", "\"sys\""),
    ),
    VendorSignature(
        VendorFamily.TELTONIKA,
        strong=("teltonika", "rutos", "rutx", "rut240"),
        weak=("package firewall", "option passwordauth", "uhttpd", "dropbear", "redirect_https"),
    ),
    VendorSignature(
        VendorFamily.QUECTEL,
        strong=("quectel", "qsslcfg", "qflock", "cgdcont"),
        weak=("sslversion", "bg95", "ec25", "at+"),
    ),
    VendorSignature(
        VendorFamily.MOXA,
        strong=("moxa", "nport", "eds-"),
        weak=("accessible ip", "\"serial\"", "modbus"),
    ),
    VendorSignature(
        VendorFamily.ADVANTECH,
        strong=("advantech", "wise-", "adam-"),
        weak=("\"modbus\"", "\"mqtt\"", "\"gpio\""),
    ),

    # Generic IoT catch-all. Deliberately LAST: its markers (mqtt, modbus,
    # bacnet) are shared with the specific OT vendors above, and equal scores
    # resolve to the earlier entry.
    VendorSignature(
        VendorFamily.IOT_EMBEDDED,
        strong=("mqtt", "modbus", "bacnet", "coap", "onvif", "zigbee", "lorawan"),
        weak=("firmware_version", "telemetry", "sensor", "device_id", "gpio", "rtsp"),
    ),
)

VENDOR_DISPLAY_NAMES: Dict[VendorFamily, str] = {
    VendorFamily.CISCO_IOS: "Cisco IOS / IOS-XE",
    VendorFamily.CISCO_NXOS: "Cisco NX-OS",
    VendorFamily.CISCO_IOSXR: "Cisco IOS-XR",
    VendorFamily.CISCO_ASA: "Cisco ASA",
    VendorFamily.CISCO_FIREPOWER: "Cisco Firepower",
    VendorFamily.JUNIPER_JUNOS: "Juniper Junos",
    VendorFamily.PALO_ALTO_PANOS: "Palo Alto PAN-OS",
    VendorFamily.FORTINET_FORTIOS: "Fortinet FortiOS",
    VendorFamily.CHECKPOINT_GAIA: "Check Point Gaia",
    VendorFamily.SOPHOS_XG: "Sophos XG",
    VendorFamily.PFSENSE: "pfSense",
    VendorFamily.ARISTA_EOS: "Arista EOS",
    VendorFamily.EXTREME_EXOS: "Extreme EXOS",
    VendorFamily.DELL_OS10: "Dell SmartFabric OS10",
    VendorFamily.SONIC: "SONiC",
    VendorFamily.AWS_SECURITY_GROUP: "AWS Security Group",
    VendorFamily.AZURE_NSG: "Azure NSG",
    VendorFamily.GCP_FIREWALL: "GCP Firewall",
    VendorFamily.HUAWEI_VRP: "Huawei VRP",
    VendorFamily.MIKROTIK_ROUTEROS: "MikroTik RouterOS",
    VendorFamily.ARUBA_AOSCX: "Aruba AOS-CX",
    VendorFamily.VYOS: "VyOS",
    VendorFamily.UBIQUITI_EDGEOS: "Ubiquiti EdgeOS",
    VendorFamily.UBIQUITI_UNIFI: "Ubiquiti UniFi",
    VendorFamily.RUCKUS_SMARTZONE: "Ruckus SmartZone",
    VendorFamily.TPLINK_OMADA: "TP-Link Omada",
    VendorFamily.ZYXEL: "Zyxel",
    VendorFamily.F5_TMOS: "F5 BIG-IP TMOS",
    VendorFamily.OPENWRT: "OpenWrt",
    VendorFamily.IOT_EMBEDDED: "IoT / Embedded",
    VendorFamily.CISCO_MERAKI: "Cisco Meraki",
    VendorFamily.ARUBA_INSTANT: "Aruba Instant",
    VendorFamily.EXTREME_WING: "Extreme WiNG",
    # Firewalls / NGFW
    VendorFamily.FORCEPOINT: "Forcepoint NGFW",
    VendorFamily.WATCHGUARD: "WatchGuard Firebox",
    VendorFamily.SONICWALL: "SonicWall SonicOS",
    VendorFamily.BARRACUDA: "Barracuda CloudGen",
    VendorFamily.HILLSTONE: "Hillstone StoneOS",
    VendorFamily.SANGFOR: "Sangfor NGAF",
    VendorFamily.KERIO: "Kerio Control",
    VendorFamily.OPNSENSE: "OPNsense",
    VendorFamily.IPTABLES: "Linux iptables",
    # Routing / switching
    VendorFamily.NOKIA_SROS: "Nokia SR OS",
    VendorFamily.H3C_COMWARE: "H3C Comware",
    VendorFamily.BROCADE_FASTIRON: "Brocade FastIron",
    VendorFamily.ALLIED_TELESIS: "Allied Telesis AlliedWare Plus",
    VendorFamily.RUIJIE_RGOS: "Ruijie RGOS",
    VendorFamily.DLINK: "D-Link",
    VendorFamily.NETGEAR: "NETGEAR ProSAFE",
    VendorFamily.ARUBA_AOSS: "Aruba AOS-S",
    VendorFamily.RUCKUS_ICX: "Ruckus ICX",
    # Wireless
    VendorFamily.MIST: "Juniper Mist",
    VendorFamily.CAMBIUM: "Cambium cnPilot",
    VendorFamily.GRANDSTREAM: "Grandstream GWN",
    VendorFamily.ENGENIUS: "EnGenius",
    VendorFamily.DRAYTEK: "DrayTek Vigor",
    # Industrial control / OT
    VendorFamily.SIEMENS: "Siemens SIMATIC",
    VendorFamily.SCHNEIDER: "Schneider Modicon",
    VendorFamily.ROCKWELL: "Rockwell ControlLogix",
    VendorFamily.MITSUBISHI: "Mitsubishi MELSEC",
    VendorFamily.OMRON: "Omron Sysmac",
    VendorFamily.BECKHOFF: "Beckhoff TwinCAT",
    VendorFamily.WAGO: "WAGO PFC",
    VendorFamily.PHOENIX_CONTACT: "Phoenix Contact PLCnext",
    VendorFamily.ABB: "ABB AC500",
    VendorFamily.EMERSON: "Emerson DeltaV",
    VendorFamily.GE_VERNOVA: "GE Vernova PACSystems",
    VendorFamily.HONEYWELL: "Honeywell Niagara",
    VendorFamily.JOHNSON_CONTROLS: "Johnson Controls Metasys",
    # Cameras / smart devices / gateways
    VendorFamily.AXIS: "Axis Communications",
    VendorFamily.HIKVISION: "Hikvision",
    VendorFamily.DAHUA: "Dahua",
    VendorFamily.HANWHA: "Hanwha Wisenet",
    VendorFamily.TASMOTA: "Tasmota",
    VendorFamily.ESPRESSIF: "Espressif ESPHome",
    VendorFamily.PARTICLE: "Particle Device OS",
    VendorFamily.SHELLY: "Shelly",
    VendorFamily.TELTONIKA: "Teltonika RutOS",
    VendorFamily.QUECTEL: "Quectel",
    VendorFamily.MOXA: "Moxa",
    VendorFamily.ADVANTECH: "Advantech WISE",
    VendorFamily.UNKNOWN: "Unknown Vendor",
}


def vendor_display_name(vendor) -> str:
    """Human-readable vendor label. Falls back to a title-cased enum value."""
    try:
        member = vendor if isinstance(vendor, VendorFamily) else VendorFamily(str(vendor))
    except ValueError:
        return str(vendor).replace("_", " ").title()
    return VENDOR_DISPLAY_NAMES.get(member, member.value.replace("_", " ").title())


_SHORT_MARKER_CACHE: Dict[str, "re.Pattern[str]"] = {}


def _marker_present(text_lower: str, marker: str) -> bool:
    """
    Test one marker against the configuration text.

    Short alphanumeric markers are matched on token boundaries rather than as
    bare substrings. Plain ``in`` testing made three-letter product prefixes
    actively harmful: ``ews`` (EnGenius) matched inside "reviews", ``zld``
    (Zyxel) and ``icx`` (Ruckus) matched inside unrelated identifiers, and each
    false hit handed the configuration to the wrong vendor.
    """
    # Only purely alphanumeric markers get boundary treatment. A marker that
    # ends in punctuation is a deliberate prefix ("wise-", "adam-") and the
    # trailing lookahead would reject the very digits it is meant to precede.
    if len(marker) <= 5 and marker.isalnum():
        pattern = _SHORT_MARKER_CACHE.get(marker)
        if pattern is None:
            pattern = re.compile(
                r"(?<![a-z0-9])" + re.escape(marker) + r"(?![a-z0-9])"
            )
            _SHORT_MARKER_CACHE[marker] = pattern
        return bool(pattern.search(text_lower))
    return marker in text_lower


def _score(text_lower: str, sig: VendorSignature) -> float:
    """Weighted, normalized match score in the range 0.0-1.0 for one vendor."""
    for veto in sig.exclude:
        if _marker_present(text_lower, veto):
            return 0.0

    strong_hits = sum(1 for m in sig.strong if _marker_present(text_lower, m))
    weak_hits = sum(1 for m in sig.weak if _marker_present(text_lower, m))

    # Co-occurrence groups: all markers in a group must appear together.
    structural_hits = sum(
        1 for group in sig.structural
        if group and all(_marker_present(text_lower, m) for m in group)
    )

    if strong_hits == 0 and weak_hits == 0 and structural_hits == 0:
        return 0.0

    earned = (
        STRONG_WEIGHT * strong_hits
        + WEAK_WEIGHT * weak_hits
        + STRUCTURAL_WEIGHT * structural_hits
    )
    possible = (
        STRONG_WEIGHT * len(sig.strong)
        + WEAK_WEIGHT * len(sig.weak)
        + STRUCTURAL_WEIGHT * len(sig.structural)
    )
    raw = earned / possible if possible else 0.0

    # Contradiction penalty: subtract for evidence pointing at a rival vendor.
    contradiction_hits = sum(1 for m in sig.contradicts if _marker_present(text_lower, m))
    return max(0.0, raw - CONTRADICTION_PENALTY * contradiction_hits)


def fingerprint_vendor_ex(raw_text: str) -> dict:
    """
    Full fingerprint result including an explicit classification status.

    Abstaining is a valid answer here. A sparse configuration that genuinely
    cannot identify its vendor returns UNKNOWN_EDGE_CASE, which is a correct
    refusal rather than a miss — and is counted separately from a confident
    wrong answer in the evaluation harness.
    """
    text = raw_text or ""
    text_lower = text.lower()
    substantive_lines = [
        ln for ln in text.splitlines()
        if ln.strip() and not ln.strip().startswith(("!", "#", "//", "/*", "<!--"))
    ]

    def result(vendor, confidence, status, runners=None, reason=None):
        return {
            "vendor": vendor,
            "vendor_display": vendor_display_name(vendor),
            "confidence": confidence,
            "classification_status": status,
            "status_reason": reason,
            "runner_up": runners or [],
        }

    if not text_lower.strip():
        return result(VendorFamily.UNKNOWN, 0.0, ClassificationStatus.UNKNOWN_EDGE_CASE,
                      reason="Configuration is empty.")

    scored = [(sig.vendor, _score(text_lower, sig)) for sig in SIGNATURES]
    scored = [(v, s) for v, s in scored if s > 0.0]

    if not scored:
        sparse = len(substantive_lines) <= SPARSE_CONFIG_LINES
        return result(
            VendorFamily.UNKNOWN, 0.0,
            ClassificationStatus.UNKNOWN_EDGE_CASE if sparse
            else ClassificationStatus.LOW_EVIDENCE,
            reason=(f"Only {len(substantive_lines)} substantive line(s); no vendor "
                    f"signature matched." if sparse
                    else "No vendor signature matched despite a substantive configuration."),
        )

    scored.sort(key=lambda vs: vs[1], reverse=True)
    best_vendor, best_score = scored[0]
    second_vendor, second_score = scored[1] if len(scored) > 1 else (None, 0.0)

    # Evidence floor: abstain rather than name a vendor on a single stray token.
    if best_score < MIN_EVIDENCE_SCORE:
        sparse = len(substantive_lines) <= SPARSE_CONFIG_LINES
        return result(
            VendorFamily.UNKNOWN, 0.0,
            ClassificationStatus.UNKNOWN_EDGE_CASE if sparse
            else ClassificationStatus.LOW_EVIDENCE,
            [{"vendor": v.value, "score": round(s, 3)} for v, s in scored[:3]],
            reason=(f"Best candidate {best_vendor.value} scored only {best_score:.3f}, "
                    f"below the {MIN_EVIDENCE_SCORE} evidence floor"
                    + (f" across {len(substantive_lines)} substantive line(s)." if sparse
                       else ".")),
        )

    confidence = 0.55 + 0.42 * best_score
    margin = ((best_score - second_score) / best_score) if best_score else 0.0
    if second_score > 0.0:
        confidence *= 0.80 + 0.20 * margin
    confidence = round(min(0.97, confidence), 2)

    runners = [
        {"vendor": v.value, "score": round(s, 3)} for v, s in scored[1:4]
    ]

    if second_score > 0.0 and margin < CONFIDENT_MARGIN:
        return result(
            best_vendor, confidence, ClassificationStatus.CONFLICTING_EVIDENCE, runners,
            reason=(f"{best_vendor.value} ({best_score:.2f}) and {second_vendor.value} "
                    f"({second_score:.2f}) score within {margin:.0%}; evidence does not "
                    f"separate them."),
        )
    if best_score < CONFIDENT_SCORE:
        return result(
            best_vendor, confidence, ClassificationStatus.LOW_EVIDENCE, runners,
            reason=(f"Best match {best_vendor.value} scored {best_score:.2f}, below the "
                    f"{CONFIDENT_SCORE:.2f} confidence threshold."),
        )
    return result(best_vendor, confidence, ClassificationStatus.CONFIDENT, runners)


def fingerprint_vendor(raw_text: str):
    """Returns (VendorFamily, confidence). Backward-compatible wrapper."""
    res = fingerprint_vendor_ex(raw_text)
    return res["vendor"], res["confidence"]


def fingerprint_vendor_detailed(raw_text: str) -> dict:
    """Diagnostic variant exposing the full ranking — useful for the UI's
    'why did you think this?' explanation and for debugging misclassification."""
    text_lower = (raw_text or "").lower()
    ranking = sorted(
        (
            (sig.vendor, _score(text_lower, sig))
            for sig in SIGNATURES
        ),
        key=lambda vs: vs[1],
        reverse=True,
    )
    vendor, confidence = fingerprint_vendor(raw_text)
    return {
        "vendor": vendor.value,
        "vendor_display": vendor_display_name(vendor),
        "confidence": confidence,
        "ranking": [
            {"vendor": v.value, "vendor_display": vendor_display_name(v), "score": round(s, 3)}
            for v, s in ranking
            if s > 0.0
        ][:5],
    }

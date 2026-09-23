"""
GAACA Dataset Generators Package
================================
Exports all vendor configuration generators across 5 categories:
Firewall (21), Routers (20), Switches (20), WiFi (20), IoT (25).
"""

from generators.base import ConfigGenerator
from generators.firewall_generators import FIREWALL_GENERATORS
from generators.router_generators import ROUTER_GENERATORS
from generators.switch_generators import SWITCH_GENERATORS
from generators.wifi_generators import WIFI_GENERATORS
from generators.iot_generators import IOT_GENERATORS

ALL_GENERATORS = {
    "firewall": FIREWALL_GENERATORS,
    "routers": ROUTER_GENERATORS,
    "switches": SWITCH_GENERATORS,
    "wifi": WIFI_GENERATORS,
    "iot": IOT_GENERATORS,
}

__all__ = [
    "ConfigGenerator",
    "FIREWALL_GENERATORS",
    "ROUTER_GENERATORS",
    "SWITCH_GENERATORS",
    "WIFI_GENERATORS",
    "IOT_GENERATORS",
    "ALL_GENERATORS",
]

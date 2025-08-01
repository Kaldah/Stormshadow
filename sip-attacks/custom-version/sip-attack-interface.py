"""
SIP Attack Module Interface
"""

from abc import ABC, abstractmethod
from typing import List


class AttackInterface(ABC):
    def __init__(self, dst_ip: str, rate: int, delay: float, sip_users: List[int], dst_port: int = 5060):
        self.rate = rate
        self.delay = delay
        self.sip_users = sip_users
        self.dst_port = dst_port

from abc import ABC, abstractmethod
from typing import List

class AttackInterface(ABC):
    def __init__(self, dst_ip: str, rate: int, delay: float, sip_users: List[int], dst_port: int = 5060):
        
        self.attack_type = "SIP"
        self.attack_name = "SIP Custom Attack"
        self.dst_ip = dst_ip
        self.dst_port = dst_port
        self.rate = rate
        self.delay = delay
        self.sip_users = sip_users


    @abstractmethod
    def run(self):
        """Start the attack"""
        pass

    @abstractmethod
    def stop(self):
        """Stop the attack (default behavior: call cleanup)"""
        print(f"[INFO] Stopping attack on {self.dst_ip}")
        self.cleanup()
        
    @abstractmethod
    def cleanup(self):
        """Default cleanup (optional override)"""
        print("[INFO] Default cleanup called (no specific cleanup implemented)")

    def get_attack_type(self) -> str:
        """Return the type of attack"""
        return self.attack_type

    def get_attack_name(self) -> str:
        """Return the name of the attack"""
        return self.attack_name

    @abstractmethod
    def get_attack_description(self) -> str:
        """Return a description of the attack"""
        return "This is a custom SIP attack module."
    
    @abstractmethod
    def load_config(self, config: dict):
        """Load configuration for the attack"""
        print("[INFO] Loading configuration for SIP attack")
        self.dst_ip = config.get("dst_ip", self.dst_ip)
        self.rate = config.get("rate", self.rate)
        self.delay = config.get("delay", self.delay)
        self.sip_users = config.get("sip_users", self.sip_users)
        self.dst_port = config.get("dst_port", self.dst_port)
        pass

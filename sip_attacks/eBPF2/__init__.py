"""
eBPF-enhanced attack modules.

This package contains advanced attack implementations using eBPF (Extended Berkeley Packet Filter)
for sophisticated packet manipulation and spoofing capabilities.
"""

from .attack_ebpf_inviteflood import EbpfInviteFloodAttack

__all__ = ['EbpfInviteFloodAttack']

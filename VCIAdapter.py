"""
   VCIAdapter.py

   Evolution XS VCI Adapter for PyPSADiag
   Uses subprocess bridge to communicate with 32-bit VCI DLL

   Copyright (C) 2025 Marc Postema (mpostema09 -at- gmail.com)

   This program is free software; you can redistribute it and/or
   modify it under the terms of the GNU General Public License
   as published by the Free Software Foundation; either version 2
   of the License, or (at your option) any later version.
"""

import json
import subprocess
import threading
import queue
import time
import os
import sys
from datetime import datetime
from PySide6.QtCore import QObject, Signal

class VCIAdapter(QObject):
    """
    Evolution XS VCI Adapter
    Communicates with 32-bit VCI DLL through subprocess bridge
    """
    
    # Signals for communication with GUI
    logSignal = Signal(str)
    packetReceivedSignal = Signal(str, str)  # command, response
    
    def __init__(self):
        super().__init__()
        self.bridge_process = None
        self.response_queue = queue.Queue()
        self.log_queue = queue.Queue()
        self.reader_thread = None
        self.connected = False
        self.configured = False
        
    def log(self, message):
        """Log message"""
        log_msg = f"[VCI] {message}"
        print(log_msg)
        self.logSignal.emit(log_msg)
    
    def start_bridge(self):
        """Start the 32-bit VCI bridge subprocess"""
        if self.bridge_process and self.bridge_process.poll() is None:
            return True
            
        try:
            # Try py launcher first (preferred method)
            try:
                # Test if py -3-32 works
                test_result = subprocess.run(
                    ["py", "-3-32", "--version"], 
                    capture_output=True, 
                    text=True, 
                    timeout=5
                )
                if test_result.returncode == 0:
                    bridge_args = ["py", "-3-32", "VCIBridge.py"]
                    self.log("Using py launcher for 32-bit Python")
                else:
                    raise subprocess.SubprocessError("py -3-32 not available")
                    
            except (subprocess.SubprocessError, subprocess.TimeoutExpired, FileNotFoundError):
                # Fallback to direct Python paths
                self.log("py launcher not available, trying direct paths...")
                python32_paths = [
                    r"C:\Python32\python.exe",
                    r"C:\Python311-32\python.exe", 
                    r"C:\Python310-32\python.exe",
                    r"C:\Python39-32\python.exe",
                    r"C:\Python38-32\python.exe",
                    "python32.exe",
                    "python.exe"  # Last resort - might be 32-bit
                ]
                
                python32_exe = None
                for path in python32_paths:
                    if os.path.exists(path):
                        python32_exe = path
                        break
                
                if python32_exe:
                    bridge_args = [python32_exe, "VCIBridge.py"]
                    self.log(f"Using direct Python path: {python32_exe}")
                else:
                    raise FileNotFoundError("No 32-bit Python installation found")
            
            # Start bridge process
            self.bridge_process = subprocess.Popen(
                bridge_args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.path.dirname(os.path.abspath(__file__)),
                bufsize=0
            )
            
            # Start reader thread
            self.reader_thread = threading.Thread(target=self._read_bridge_output, daemon=True)
            self.reader_thread.start()
            
            self.log("VCI Bridge started")
            time.sleep(1)  # Give bridge time to initialize
            return True
            
        except Exception as e:
            self.log(f"Failed to start VCI bridge: {e}")
            return False
    
    def stop_bridge(self):
        """Stop the VCI bridge subprocess"""
        if self.bridge_process:
            try:
                # Send quit command
                self._send_command("quit")
                
                # Wait for process to terminate
                self.bridge_process.wait(timeout=5)
                
            except subprocess.TimeoutExpired:
                self.log("Bridge didn't stop gracefully, terminating")
                self.bridge_process.terminate()
                self.bridge_process.wait(timeout=2)
                
            except Exception as e:
                self.log(f"Error stopping bridge: {e}")
                
            finally:
                self.bridge_process = None
                
        self.connected = False
        self.configured = False
        self.log("VCI Bridge stopped")
    
    def _read_bridge_output(self):
        """Read output from bridge subprocess"""
        try:
            while self.bridge_process and self.bridge_process.poll() is None:
                line = self.bridge_process.stdout.readline()
                if not line:
                    break
                    
                try:
                    response = json.loads(line.strip())
                    command = response.get("command")
                    data = response.get("data", {})
                    
                    if command == "log":
                        self.log(data.get("message", ""))
                    else:
                        self.response_queue.put(response)
                        
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    self.log(f"Error processing bridge response: {e}")
                    
        except Exception as e:
            self.log(f"Bridge reader thread error: {e}")
    
    def _send_command(self, command, params=None, timeout=10):
        """Send command to bridge and wait for response"""
        if not self.bridge_process or self.bridge_process.poll() is not None:
            self.log("Bridge process not running")
            return None
            
        try:
            cmd_data = {
                "command": command,
                "params": params or {},
                "timestamp": datetime.now().isoformat()
            }
            
            # Send command
            cmd_json = json.dumps(cmd_data) + "\n"
            self.bridge_process.stdin.write(cmd_json)
            self.bridge_process.stdin.flush()
            
            # Wait for response
            expected_response = f"{command}_response"
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    response = self.response_queue.get(timeout=1)
                    if response.get("command") == expected_response:
                        return response.get("data")
                except queue.Empty:
                    continue
                    
            self.log(f"Command {command} timed out")
            return None
            
        except Exception as e:
            self.log(f"Error sending command {command}: {e}")
            return None
    
    def connect(self):
        """Connect to VCI"""
        if not self.start_bridge():
            return False
            
        response = self._send_command("connect")
        if response and response.get("success"):
            self.connected = True
            self.log("Connected to Evolution XS VCI")
            return True
        else:
            self.log("Failed to connect to VCI")
            return False
    
    def disconnect(self):
        """Disconnect from VCI"""
        if self.connected:
            response = self._send_command("disconnect")
            if response and response.get("success"):
                self.log("Disconnected from VCI")
            else:
                self.log("Error disconnecting from VCI")
                
        self.stop_bridge()
        return True
    
    def configure(self, tx_id, rx_id, protocol="uds", bus="DIAG", target=None, dialog_type="0"):
        """Configure VCI for ECU communication"""
        if not self.connected:
            if not self.connect():
                return False
        
        # Map PyPSADiag protocol names to VCI protocols
        protocol_map = {
            "uds": "DIAGONCAN",
            "kwp_is": "DIAGONCAN", 
            "kwp_hab": "DIAGONCAN",
            "kwp2000": "PSA2000",
            "psa2000": "PSA2000",
            "fiat_kwp": "KWPONCAN_FIAT"
        }
        
        vci_protocol = protocol_map.get(protocol.lower(), "DIAGONCAN")
        
        # Auto-detect bus type based on protocol if not specified
        if bus == "auto":
            if protocol.lower() in ["kwp_is"]:
                vci_bus = "IS"
            else:
                vci_bus = "DIAG"
        else:
            vci_bus = "IS" if bus == "IS" else "DIAG"
        
        params = {
            "tx_h": tx_id,
            "rx_h": rx_id,
            "bus": vci_bus,
            "protocol": vci_protocol
        }
        
        # Add optional parameters for specific protocols
        if target is not None:
            params["target"] = target
        if dialog_type != "0":
            params["dialog_type"] = dialog_type
        
        response = self._send_command("configure", params)
        if response and response.get("success"):
            self.configured = True
            self.log(f"VCI configured: {tx_id}:{rx_id} on {vci_bus} using {vci_protocol}")
            return True
        else:
            self.log("Failed to configure VCI")
            return False
    
    def send_receive(self, data, timeout=1500):
        """Send data to ECU and receive response"""
        if not self.configured:
            self.log("VCI not configured")
            return ""
            
        params = {
            "data": data,
            "timeout": timeout
        }
        
        response = self._send_command("send_receive", params)
        if response:
            result = response.get("response", "")
            if result:
                self.packetReceivedSignal.emit(data, result)
            return result
        else:
            self.log("Send/Receive failed")
            return ""
    
    def is_connected(self):
        """Check if VCI is connected"""
        return self.connected
    
    def is_configured(self):
        """Check if VCI is configured"""
        return self.configured
    
    def send_receive_multiple(self, data, responses=1, timeout=1500):
        """Send data and receive multiple responses (for KWP2000 protocols)"""
        if not self.configured:
            self.log("VCI not configured")
            return ""
            
        params = {
            "data": data,
            "responses": responses,
            "timeout": timeout
        }
        
        response = self._send_command("send_receive_multiple", params)
        if response:
            result = response.get("response", "")
            if result:
                self.packetReceivedSignal.emit(data, result)
            return result
        else:
            self.log("Send/Receive Multiple failed")
            return ""
    
    def perform_ecu_init(self):
        """Perform ECU initialization (for KWP2000/PSA2 protocols)"""
        if not self.configured:
            self.log("VCI not configured")
            return False
            
        response = self._send_command("perform_init")
        if response and response.get("success"):
            self.log("ECU initialization successful")
            return True
        else:
            self.log("ECU initialization failed")
            return False
    
    def get_analog_voltage(self, channel=0):
        """Get analog voltage reading from VCI"""
        if not self.connected:
            self.log("VCI not connected")
            return None
            
        params = {"channel": channel}
        response = self._send_command("get_analog_data", params)
        if response:
            voltage = response.get("voltage")
            if voltage is not None:
                self.log(f"Analog channel {channel}: {voltage:.2f}V")
            return voltage
        else:
            self.log("Analog data read failed")
            return None
    
    def get_adapter_info(self):
        """Get adapter information"""
        return {
            "name": "Evolution XS VCI",
            "type": "VCI",
            "connected": self.connected,
            "configured": self.configured,
            "features": [
                "UDS Protocol",
                "KWP2000 Protocol", 
                "CAN DIAG Bus",
                "CAN I/S Bus",
                "Multiple Frame Support",
                "Analog Voltage Reading",
                "ECU Initialization"
            ]
        }
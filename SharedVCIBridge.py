"""
SharedVCIBridge.py

Shared VCI Bridge Manager - Allows multiple PyPSA components to share VCI access
Solves the problem of VCI-blocking between main program and enhanced features

Copyright (C) 2025 PyPSA Enhanced - VCI Bridge Sharing Solution
"""

import sys
import os
import json
import threading
import time
import queue
import socket
import subprocess
from datetime import datetime

class SharedVCIBridge:
    """
    Shared VCI Bridge that allows multiple clients to access VCI simultaneously
    Acts as a server that manages VCI access requests from different components
    """
    
    def __init__(self, port=9999):
        self.port = port
        self.vci_bridge_process = None
        self.vci_response_queue = queue.Queue()
        self.clients = {}
        self.request_queue = queue.Queue()
        self.running = False
        self.server_socket = None
        self.vci_lock = threading.Lock()
        self.current_client = None
        self.vci_connected = False
        
    def _start_vci_bridge_process(self):
        """Start 32-bit VCI bridge subprocess"""
        if self.vci_bridge_process and self.vci_bridge_process.poll() is None:
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
                    print("[SharedVCI] Using py launcher for 32-bit Python")
                else:
                    raise subprocess.SubprocessError("py -3-32 not available")
                    
            except (subprocess.SubprocessError, subprocess.TimeoutExpired, FileNotFoundError):
                # Fallback to direct Python paths
                print("[SharedVCI] py launcher not available, trying direct paths...")
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
                    print(f"[SharedVCI] Using direct Python path: {python32_exe}")
                else:
                    raise FileNotFoundError("No 32-bit Python installation found")
            
            # Start bridge process
            self.vci_bridge_process = subprocess.Popen(
                bridge_args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.path.dirname(os.path.abspath(__file__)),
                bufsize=0
            )
            
            # Start reader thread for VCI bridge
            vci_reader_thread = threading.Thread(target=self._read_vci_bridge_output, daemon=True)
            vci_reader_thread.start()
            
            print("[SharedVCI] VCI Bridge subprocess started")
            time.sleep(2)  # Give bridge time to initialize
            return True
            
        except Exception as e:
            print(f"[SharedVCI] Failed to start VCI bridge: {e}")
            return False
    
    def _read_vci_bridge_output(self):
        """Read output from VCI bridge subprocess"""
        try:
            while self.vci_bridge_process and self.vci_bridge_process.poll() is None:
                line = self.vci_bridge_process.stdout.readline()
                if not line:
                    break
                    
                try:
                    response = json.loads(line.strip())
                    command = response.get("command")
                    data = response.get("data", {})
                    
                    if command == "log":
                        print(f"[VCI-Bridge] {data.get('message', '')}")
                    else:
                        self.vci_response_queue.put(response)
                        
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    print(f"[SharedVCI] Error processing VCI bridge response: {e}")
                    
        except Exception as e:
            print(f"[SharedVCI] VCI bridge reader thread error: {e}")
    
    def _send_vci_command(self, command, params=None, timeout=10):
        """Send command to VCI bridge and wait for response"""
        if not self.vci_bridge_process or self.vci_bridge_process.poll() is not None:
            print("[SharedVCI] VCI bridge process not running")
            return None
            
        try:
            cmd_data = {
                "command": command,
                "params": params or {},
                "timestamp": datetime.now().isoformat()
            }
            
            # Send command
            cmd_json = json.dumps(cmd_data) + "\n"
            self.vci_bridge_process.stdin.write(cmd_json)
            self.vci_bridge_process.stdin.flush()
            
            # Wait for response
            expected_response = f"{command}_response"
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    response = self.vci_response_queue.get(timeout=1)
                    if response.get("command") == expected_response:
                        return response.get("data")
                except queue.Empty:
                    continue
                    
            print(f"[SharedVCI] VCI command {command} timed out")
            return None
            
        except Exception as e:
            print(f"[SharedVCI] Error sending VCI command {command}: {e}")
            return None
    
    def _stop_vci_bridge_process(self):
        """Stop VCI bridge subprocess"""
        if self.vci_bridge_process:
            try:
                # Send quit command
                self._send_vci_command("quit")
                
                # Wait for process to terminate
                self.vci_bridge_process.wait(timeout=5)
                
            except subprocess.TimeoutExpired:
                print("[SharedVCI] VCI bridge didn't stop gracefully, terminating")
                self.vci_bridge_process.terminate()
                self.vci_bridge_process.wait(timeout=2)
                
            except Exception as e:
                print(f"[SharedVCI] Error stopping VCI bridge: {e}")
                
            finally:
                self.vci_bridge_process = None
                
        self.vci_connected = False

    def start_server(self):
        """Start the VCI bridge sharing server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('localhost', self.port))
            self.server_socket.listen(5)
            self.running = True
            
            print(f"SharedVCIBridge Server started on port {self.port}")
            
            # Start request handler thread
            handler_thread = threading.Thread(target=self._handle_requests)
            handler_thread.daemon = True
            handler_thread.start()
            
            # Accept client connections
            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    client_id = f"client_{len(self.clients)}"
                    self.clients[client_id] = {
                        'socket': client_socket,
                        'address': address,
                        'last_activity': time.time()
                    }
                    
                    # Handle client in separate thread
                    client_thread = threading.Thread(
                        target=self._handle_client, 
                        args=(client_id, client_socket)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                    print(f"Client {client_id} connected from {address}")
                    
                except socket.error as e:
                    if self.running:
                        print(f"Server socket error: {e}")
                        break
                        
        except Exception as e:
            print(f"Failed to start SharedVCIBridge server: {e}")
            
    def _handle_client(self, client_id, client_socket):
        """Handle individual client requests"""
        try:
            while self.running:
                try:
                    # Receive request from client
                    data = client_socket.recv(4096).decode('utf-8')
                    if not data:
                        break
                        
                    request = json.loads(data)
                    request['client_id'] = client_id
                    request['timestamp'] = time.time()
                    
                    # Add to request queue
                    self.request_queue.put(request)
                    
                    # Update client activity
                    if client_id in self.clients:
                        self.clients[client_id]['last_activity'] = time.time()
                        
                except socket.error:
                    break
                except json.JSONDecodeError:
                    # Send error response
                    error_response = {
                        'status': 'error',
                        'message': 'Invalid JSON request'
                    }
                    self._send_response(client_socket, error_response)
                    
        except Exception as e:
            print(f"Error handling client {client_id}: {e}")
        finally:
            # Clean up client
            if client_id in self.clients:
                del self.clients[client_id]
            try:
                client_socket.close()
            except:
                pass
            print(f"Client {client_id} disconnected")
            
    def _handle_requests(self):
        """Process VCI requests from clients"""
        while self.running:
            try:
                # Get request from queue (timeout to allow checking self.running)
                request = self.request_queue.get(timeout=1.0)
                
                with self.vci_lock:
                    response = self._process_vci_request(request)
                
                # Send response back to client
                client_id = request['client_id']
                if client_id in self.clients:
                    client_socket = self.clients[client_id]['socket']
                    self._send_response(client_socket, response)
                    
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error processing request: {e}")
                
    def _process_vci_request(self, request):
        """Process individual VCI request"""
        try:
            command = request.get('command')
            params = request.get('params', {})
            client_id = request['client_id']
            
            # Handle different VCI commands
            if command == 'connect':
                return self._handle_connect(client_id, params)
            elif command == 'disconnect':
                return self._handle_disconnect(client_id)
            elif command == 'configure_ecu':
                return self._handle_configure_ecu(params)
            elif command == 'send_request':
                return self._handle_send_request(params)
            elif command == 'get_status':
                return self._handle_get_status()
            else:
                return {
                    'status': 'error',
                    'message': f'Unknown command: {command}'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Request processing error: {str(e)}'
            }
            
    def _handle_connect(self, client_id, params):
        """Handle VCI connection request"""
        try:
            if not self.vci_connected:
                # Start VCI bridge process if not running
                if not self._start_vci_bridge_process():
                    return {
                        'status': 'error',
                        'message': 'Failed to start VCI bridge process'
                    }
                
                # Connect to VCI through subprocess
                connect_result = self._send_vci_command("connect")
                if not connect_result or not connect_result.get("success"):
                    return {
                        'status': 'error',
                        'message': 'Failed to connect to VCI'
                    }
                
                self.vci_connected = True
                
            self.current_client = client_id
            return {
                'status': 'success',
                'message': 'VCI connected',
                'client_id': client_id
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Connection failed: {str(e)}'
            }
            
    def _handle_disconnect(self, client_id):
        """Handle VCI disconnection request"""
        try:
            if self.current_client == client_id:
                self.current_client = None
                
            return {
                'status': 'success',
                'message': 'Disconnected'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Disconnection failed: {str(e)}'
            }
            
    def _handle_configure_ecu(self, params):
        """Handle ECU configuration request"""
        try:
            ecu_config = params.get('ecu_config')
            if not ecu_config:
                return {
                    'status': 'error',
                    'message': 'ECU configuration required'
                }
                
            # Configure VCI for ECU using VCI subprocess
            config_params = {
                'tx_h': ecu_config.get('tx_id', '752'),
                'rx_h': ecu_config.get('rx_id', '652'),
                'protocol': ecu_config.get('protocol', 'DIAGONCAN'),
                'bus': ecu_config.get('bus', 'DIAG'),
                'target': ecu_config.get('target'),
                'dialog_type': ecu_config.get('dialog_type', '0')
            }
            
            result = self._send_vci_command("configure", config_params)
            
            return {
                'status': 'success' if result and result.get('success') else 'error',
                'message': 'ECU configured' if result and result.get('success') else 'ECU configuration failed'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'ECU configuration error: {str(e)}'
            }
            
    def _handle_send_request(self, params):
        """Handle diagnostic request"""
        try:
            service_id = params.get('service_id')
            data = params.get('data', [])
            timeout = params.get('timeout', 1500)
            
            if not service_id:
                return {
                    'status': 'error',
                    'message': 'Service ID required'
                }
                
            # Convert service_id and data to hex string format for VCIBridge
            if isinstance(data, list) and len(data) > 0:
                data_hex = ''.join([f'{b:02X}' for b in data])
                request_data = service_id + data_hex
            else:
                request_data = service_id
                
            # Send diagnostic request via VCI subprocess
            send_params = {
                'data': request_data,
                'timeout': timeout
            }
            result = self._send_vci_command("send_receive", send_params)
            
            return {
                'status': 'success' if result and result.get('response') else 'error',
                'message': 'Request sent' if result and result.get('response') else 'Request failed',
                'response': result.get('response') if result else None
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Request error: {str(e)}'
            }
            
    def _handle_get_status(self):
        """Handle status request"""
        return {
            'status': 'success',
            'vci_connected': self.vci_connected,
            'vci_bridge_running': self.vci_bridge_process and self.vci_bridge_process.poll() is None,
            'active_clients': len(self.clients),
            'current_client': self.current_client,
            'uptime': time.time() - getattr(self, 'start_time', time.time())
        }
        
    def _send_response(self, client_socket, response):
        """Send response back to client"""
        try:
            response_json = json.dumps(response)
            client_socket.send(response_json.encode('utf-8'))
        except Exception as e:
            print(f"Failed to send response: {e}")
            
    def stop_server(self):
        """Stop the VCI bridge server"""
        self.running = False
        
        # Stop VCI bridge subprocess
        self._stop_vci_bridge_process()
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        print("SharedVCIBridge Server stopped")

class SharedVCIClient:
    """
    Client for communicating with SharedVCIBridge server
    Used by both main program and enhanced features
    """
    
    def __init__(self, server_port=9999):
        self.server_port = server_port
        self.socket = None
        self.connected = False
        
    def connect_to_server(self):
        """Connect to SharedVCI server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect(('localhost', self.server_port))
            self.connected = True
            return True
        except Exception as e:
            print(f"Failed to connect to SharedVCI server: {e}")
            return False
            
    def disconnect_from_server(self):
        """Disconnect from SharedVCI server"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.connected = False
        
    def send_request(self, command, params=None):
        """Send request to SharedVCI server"""
        if not self.connected:
            return {'status': 'error', 'message': 'Not connected to server'}
            
        try:
            request = {
                'command': command,
                'params': params or {},
                'timestamp': time.time()
            }
            
            # Send request
            request_json = json.dumps(request)
            self.socket.send(request_json.encode('utf-8'))
            
            # Receive response
            response_data = self.socket.recv(4096).decode('utf-8')
            response = json.loads(response_data)
            
            return response
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Request failed: {str(e)}'
            }
            
    def connect_vci(self):
        """Connect to VCI through shared bridge"""
        return self.send_request('connect')
        
    def disconnect_vci(self):
        """Disconnect from VCI through shared bridge"""
        return self.send_request('disconnect')
        
    def configure_ecu(self, ecu_config):
        """Configure ECU through shared bridge"""
        return self.send_request('configure_ecu', {'ecu_config': ecu_config})
        
    def send_diagnostic_request(self, service_id, data=None):
        """Send diagnostic request through shared bridge"""
        return self.send_request('send_request', {
            'service_id': service_id,
            'data': data or []
        })
        
    def get_status(self):
        """Get VCI status through shared bridge"""
        return self.send_request('get_status')

def start_shared_vci_server():
    """Start the SharedVCI server as standalone process"""
    server = SharedVCIBridge()
    server.start_time = time.time()
    
    try:
        print("Starting SharedVCI Bridge Server...")
        server.start_server()
    except KeyboardInterrupt:
        print("\\nShutting down SharedVCI Bridge Server...")
        server.stop_server()
    except Exception as e:
        print(f"SharedVCI Bridge Server error: {e}")
        server.stop_server()

if __name__ == "__main__":
    # Run as standalone server
    start_shared_vci_server()
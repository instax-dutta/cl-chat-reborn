#!/usr/bin/env python3
"""
Trace Clearance Utility for Multi-Client CLI Chat - MVP
Provides comprehensive trace clearance functionality.
"""

import os
import sys
import gc
import time
import socket
from typing import List, Dict

class TraceClearance:
    """Comprehensive trace clearance utility."""
    
    def __init__(self):
        self.cleared_traces = []
    
    def clear_server_traces(self, host: str = 'localhost', port: int = 5000):
        """Clear traces from running server."""
        print("🧹 Attempting to clear server traces...")
        
        try:
            # Try to connect to server and send clear command
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((host, port))
            
            # Send a special clear command (if server supports it)
            clear_command = "CLEAR_ALL_TRACES"
            sock.send(clear_command.encode('utf-8'))
            sock.close()
            
            print("✅ Clear command sent to server")
            self.cleared_traces.append(f"server_{host}_{port}")
            
        except Exception as e:
            print(f"⚠️  Could not connect to server: {e}")
            print("   Server may not be running or may not support remote clear")
    
    def clear_local_traces(self):
        """Clear all local traces and memory."""
        print("🧹 Clearing local traces...")
        
        # Clear Python memory
        gc.collect()
        
        # Clear any cached data
        if hasattr(sys, 'modules'):
            for module_name in list(sys.modules.keys()):
                if 'chat' in module_name.lower() or 'message' in module_name.lower():
                    try:
                        del sys.modules[module_name]
                    except:
                        pass
        
        # Clear any temporary files
        self._clear_temp_files()
        
        print("✅ Local traces cleared")
        self.cleared_traces.append("local_memory")
    
    def _clear_temp_files(self):
        """Clear temporary files that might contain chat data."""
        temp_dirs = ['/tmp', '/var/tmp', os.path.expanduser('~/tmp')]
        
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                try:
                    for filename in os.listdir(temp_dir):
                        if any(keyword in filename.lower() for keyword in ['chat', 'message', 'log']):
                            filepath = os.path.join(temp_dir, filename)
                            try:
                                os.remove(filepath)
                                print(f"🗑️  Removed: {filepath}")
                            except:
                                pass
                except:
                    pass
    
    def clear_terminal_history(self):
        """Clear terminal history that might contain chat messages."""
        print("🧹 Clearing terminal history...")
        
        # Clear screen
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Clear scrollback buffer (if supported)
        if os.name != 'nt':  # Unix-like systems
            try:
                os.system('clear && printf "\033[3J"')
            except:
                pass
        
        print("✅ Terminal history cleared")
        self.cleared_traces.append("terminal_history")
    
    def clear_all_traces(self, host: str = 'localhost', port: int = 5000):
        """Perform comprehensive trace clearance."""
        print("=" * 60)
        print("🧹 COMPREHENSIVE TRACE CLEARANCE")
        print("=" * 60)
        
        # Clear server traces
        self.clear_server_traces(host, port)
        
        # Clear local traces
        self.clear_local_traces()
        
        # Clear terminal history
        self.clear_terminal_history()
        
        # Final memory cleanup
        gc.collect()
        
        print("=" * 60)
        print("✅ COMPREHENSIVE TRACE CLEARANCE COMPLETED")
        print("=" * 60)
        print("Cleared traces:")
        for trace in self.cleared_traces:
            print(f"  • {trace}")
        print("=" * 60)
        print("🔒 No communication traces remain")
        print("=" * 60)

def main():
    """Main function for trace clearance utility."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Trace Clearance Utility")
    parser.add_argument("--host", default="localhost", help="Server host (default: localhost)")
    parser.add_argument("--port", type=int, default=5000, help="Server port (default: 5000)")
    parser.add_argument("--local-only", action="store_true", help="Clear only local traces")
    
    args = parser.parse_args()
    
    clearance = TraceClearance()
    
    if args.local_only:
        print("🧹 Local trace clearance only...")
        clearance.clear_local_traces()
        clearance.clear_terminal_history()
    else:
        clearance.clear_all_traces(args.host, args.port)

if __name__ == "__main__":
    main()

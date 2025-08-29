#!/usr/bin/env python3
"""
Test script for Confluxus
Helps verify that the chat system is working correctly.
"""

import socket
import threading
import time
import json
import sys

def test_server_connection(host='localhost', port=5000):
    """Test if server is running and accepting connections."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✅ Server connection test PASSED - {host}:{port} is reachable")
            return True
        else:
            print(f"❌ Server connection test FAILED - {host}:{port} is not reachable")
            return False
    except Exception as e:
        print(f"❌ Server connection test ERROR - {e}")
        return False

def test_client_communication(host='localhost', port=5000):
    """Test basic client-server communication."""
    try:
        # Create test client
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        
        # Send username
        test_username = "TestUser"
        sock.send(test_username.encode('utf-8'))
        
        # Wait for response
        response = sock.recv(1024).decode('utf-8')
        sock.close()
        
        if response:
            try:
                data = json.loads(response)
                if data.get("type") == "error":
                    print(f"❌ Client communication test FAILED - {data['message']}")
                    return False
                elif data.get("type") == "system":
                    print(f"✅ Client communication test PASSED - Server responded correctly")
                    return True
            except json.JSONDecodeError:
                print(f"✅ Client communication test PASSED - Server responded (plain text)")
                return True
        else:
            print("❌ Client communication test FAILED - No response from server")
            return False
            
    except Exception as e:
        print(f"❌ Client communication test ERROR - {e}")
        return False

def test_port_availability(port=5000):
    """Test if port is available for binding."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('localhost', port))
        sock.close()
        print(f"✅ Port {port} is available for binding")
        return True
    except socket.error:
        print(f"❌ Port {port} is already in use")
        return False

def run_basic_tests():
    """Run all basic tests."""
    print("🧪 Running Confluxus Tests")
    print("=" * 50)
    
    # Test 1: Port availability
    print("\n1. Testing port availability...")
    port_available = test_port_availability(5000)
    
    # Test 2: Server connection (if port is available, server might not be running)
    print("\n2. Testing server connection...")
    server_connected = test_server_connection()
    
    # Test 3: Client communication (only if server is running)
    print("\n3. Testing client communication...")
    if server_connected:
        client_working = test_client_communication()
    else:
        print("⏭️  Skipping client communication test (server not running)")
        client_working = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"   Port Availability: {'✅ PASS' if port_available else '❌ FAIL'}")
    print(f"   Server Connection: {'✅ PASS' if server_connected else '❌ FAIL'}")
    print(f"   Client Communication: {'✅ PASS' if client_working else '❌ FAIL'}")
    
    if port_available and server_connected and client_working:
        print("\n🎉 All tests PASSED! Your chat system is ready to use.")
        print("\nNext steps:")
        print("1. Start the server: python server.py")
        print("2. Connect clients: python client.py --username YourName")
    elif not port_available:
        print("\n⚠️  Port 5000 is in use. Try:")
        print("   - Kill existing process: lsof -ti:5000 | xargs kill -9")
        print("   - Or use different port: python server.py --port 5001")
    elif not server_connected:
        print("\n⚠️  Server is not running. Start it with:")
        print("   python server.py")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")

def main():
    """Main test function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Confluxus Chat System")
    parser.add_argument("--host", default="localhost", help="Server host to test")
    parser.add_argument("--port", type=int, default=5000, help="Server port to test")
    
    args = parser.parse_args()
    
    print(f"Testing chat system on {args.host}:{args.port}")
    run_basic_tests()

if __name__ == "__main__":
    main()

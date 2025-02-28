import socket
import psutil
import os
import platform
import subprocess
import netifaces as ni

# Get all network interfaces
interfaces = ni.interfaces()
print(f"Interfaces: {interfaces}")

# Find the first interface that has an IPv4 address
interface_found = False
for iface in interfaces:
    try:
        ip = ni.ifaddresses(iface)[ni.AF_INET][0]['addr']
        print(f"IP Address of {iface}: {ip}")
        interface_found = True
        break
    except KeyError:
        continue

if not interface_found:
    print("No IPv4 address found for any interface.")

# Run system command to get network info (Linux example)
try:
    result = subprocess.run(['ifconfig'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode == 0:
        print(result.stdout.decode())
    else:
        print(f"Error running ifconfig: {result.stderr.decode()}")
except PermissionError:
    print("Permission denied while running ifconfig.")
except FileNotFoundError:
    print("ifconfig command not found.")

# CPU usage
try:
    cpu_percent = psutil.cpu_percent(interval=1)
    print(f"CPU Usage: {cpu_percent}%")
except PermissionError:
    print("Permission denied while accessing CPU info.")

# Memory usage
try:
    memory_info = psutil.virtual_memory()
    print(f"Memory Usage: {memory_info.percent}%")
except PermissionError:
    print("Permission denied while accessing memory info.")

# Disk usage
disk_info = psutil.disk_usage('/')
print(f"Disk Usage: {disk_info.percent}%")

# Network info
network_info = psutil.net_if_addrs()
print(f"Network Interfaces: {network_info}")

# System hostname
hostname = os.uname()
print(f"System hostname: {hostname}")

# Environment variables
env_vars = os.environ
print(f"Environment Variables: {env_vars}")

# Get hostname and IP address
hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)

print(f"Hostname: {hostname}")
print(f"IP Address: {ip_address}")

# Display network interfaces and their IPs
for interface_name, interface_addresses in psutil.net_if_addrs().items():
    print(f"Interface: {interface_name}")
    for address in interface_addresses:
        if address.family == socket.AF_INET:
            print(f"  IP Address: {address.address}")
        elif address.family == socket.AF_PACKET:
            print(f"  MAC Address: {address.address}")

# Get system information
system_info = platform.system()
version_info = platform.version()
architecture = platform.architecture()

print(f"System: {system_info}")
print(f"Version: {version_info}")
print(f"Architecture: {architecture}")
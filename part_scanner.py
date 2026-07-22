import socket

def scan_port(target, port):
    print(f"Scanning {target} on port {port}...")
    
    # Set up a network socket connection (IPv4, TCP)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3.0)  # Stop waiting after 3 seconds if there is no response
    
    # Try connecting to the port (returns 0 if successful/open)
    result = s.connect_ex((target, port))
    
    if result == 0:
        print(f"[+] Port {port} is OPEN! (The service is running)")
    else:
        print(f"[-] Port {port} is CLOSED or unreachable.")
        
    # Close the connection safely
    s.close()

if __name__ == "__main__":
    # We are scanning the legal Nmap test server on Port 80 (the web port)
    scan_port("scanme.nmap.org", 80)


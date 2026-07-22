import subprocess

def check_network(host):
    print(f"Testing connectivity to {host}...")
    result = subprocess.run(["ping", "-c", "3", host], capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"[+] Success: {host} is alive!")
        print("\nPing Output:")
        print(result.stdout)
    else:
        print(f"[-] Error: Could not reach {host}.")
        print(result.stderr)

if __name__ == "__main__":
    check_network("8.8.8.8")


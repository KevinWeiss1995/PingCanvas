import subprocess

def traceroute(host, max_hops=30, timeout=2, ipv6=False):
    """
    Perform a traceroute to a host and return the path.

    :param host: The host to traceroute.
    :param max_hops: Maximum number of hops to trace.
    :param timeout: Timeout in seconds for each hop.
    :param ipv6: Boolean indicating whether to use IPv6.
    :return: List of hops with their respective IP addresses and round-trip times.
    """
    try:
        traceroute_cmd = "traceroute6" if ipv6 else "traceroute"
        
        result = subprocess.run(
            [traceroute_cmd, "-m", str(max_hops), "-w", str(timeout), host],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode == 0:
            hops = []
            for line in result.stdout.splitlines():
                if line.startswith("traceroute") or not line.strip():
                    continue
                parts = line.split()
                hop_number = parts[0]
                hop_ip = parts[1]
                rtt = parts[2:]
                hops.append((hop_number, hop_ip, rtt))
            return hops
        else:
            return None
    except Exception as e:
        return None


if __name__ == "__main__":
    host = "8.8.8.8"  # Google
    hops = traceroute(host)
    if hops is not None:
        for hop in hops:
            print(f"Hop {hop[0]}: {hop[1]} - RTT: {hop[2]}")
    else:
        print(f"Failed to traceroute {host}")

    ipv6_host = "2001:4860:4860::8888"  # Google
    hops_ipv6 = traceroute(ipv6_host, ipv6=True)
    if hops_ipv6 is not None:
        for hop in hops_ipv6:
            print(f"Hop {hop[0]}: {hop[1]} - RTT: {hop[2]}")
    else:
        print(f"Failed to traceroute {ipv6_host}")

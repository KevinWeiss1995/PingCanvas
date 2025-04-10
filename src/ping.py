import subprocess

def ping(host, count=4, timeout=2, ipv6=False):
    """
    Ping a host and return the average round-trip time.

    :param host: The host to ping.
    :param count: Number of ping requests to send.
    :param timeout: Timeout in seconds for each ping request.
    :param ipv6: Boolean indicating whether to use IPv6.
    :return: Average round-trip time in milliseconds or None if the ping fails.
    """
    try:
        ping_cmd = "ping6" if ipv6 else "ping"
        
        result = subprocess.run(
            [ping_cmd, "-c", str(count), "-W", str(timeout), host],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode == 0:

            for line in result.stdout.splitlines():
                if "avg" in line:
                    avg_time = line.split('/')[4]
                    return float(avg_time)
        else:
            return None
    except Exception as e:
        return None

if __name__ == "__main__":
    host = "8.8.8.8" # Google
    avg_rtt = ping(host)
    if avg_rtt is not None:
        print(f"Average round-trip time to {host}: {avg_rtt} ms")
    else:
        print(f"Failed to ping {host}")

    ipv6_host = "2001:4860:4860::8888" # Google
    avg_rtt_ipv6 = ping(ipv6_host, ipv6=True)
    if avg_rtt_ipv6 is not None:
        print(f"Average round-trip time to {ipv6_host}: {avg_rtt_ipv6} ms")
    else:
        print(f"Failed to ping {ipv6_host}")

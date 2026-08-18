#!/usr/bin/env python3
"""DNS request logger/proxy.

Listens for incoming DNS queries, forwards each one to an upstream resolver
and relays the response back to the client (so it doesn't break resolution
for anything using this as its DNS server). While doing so it tracks:
  - a Counter of queried domain names ("urls")
  - a Counter of client source IPs

Counters are dumped to a JSON file periodically (and on exit), and a live
log + summary is printed to the screen.

Usage:
    sudo python3 dns_logger.py --port 53 --upstream 1.1.1.1
    python3 dns_logger.py --port 5053 --upstream 8.8.8.8   # unprivileged test
"""

from __future__ import annotations

import argparse
import json
import signal
import socket
import struct
import sys
import threading
from collections import Counter
from datetime import datetime
from pathlib import Path

DNS_HEADER_LEN = 12

QTYPES = {
    1: "A", 2: "NS", 5: "CNAME", 6: "SOA", 12: "PTR", 15: "MX", 16: "TXT",
    28: "AAAA", 33: "SRV", 41: "OPT", 65: "HTTPS", 255: "ANY",
}


def parse_qname(data: bytes, offset: int) -> tuple[str, int]:
    """Decode a (possibly compressed) domain name starting at offset.

    Returns the decoded name and the offset just past the name in the
    original message (not following any compression pointer).
    """
    labels = []
    pos = offset
    end_offset = None

    while True:
        if pos >= len(data):
            raise ValueError("Truncated DNS name")
        length = data[pos]

        if length == 0:
            pos += 1
            if end_offset is None:
                end_offset = pos
            break

        if length & 0xC0 == 0xC0:
            if pos + 1 >= len(data):
                raise ValueError("Truncated DNS pointer")
            if end_offset is None:
                end_offset = pos + 2
            pos = ((length & 0x3F) << 8) | data[pos + 1]
            continue

        pos += 1
        labels.append(data[pos:pos + length].decode("ascii", errors="replace"))
        pos += length

    return ".".join(labels), end_offset


def parse_query(data: bytes) -> tuple[str, int, int] | None:
    """Extract the first question's (qname, qtype, qclass) from a DNS message."""
    if len(data) < DNS_HEADER_LEN:
        return None
    qdcount = struct.unpack("!H", data[4:6])[0]
    if qdcount < 1:
        return None
    try:
        qname, offset = parse_qname(data, DNS_HEADER_LEN)
        qtype, qclass = struct.unpack_from("!HH", data, offset)
    except (struct.error, ValueError, IndexError):
        return None
    return qname, qtype, qclass


class DNSLoggerServer:
    def __init__(self, host, port, upstream, upstream_port, dump_file, dump_interval, top):
        self.host = host
        self.port = port
        self.upstream = upstream
        self.upstream_port = upstream_port
        self.dump_file = Path(dump_file)
        self.dump_interval = dump_interval
        self.top = top

        self.url_counter: Counter[str] = Counter()
        self.ip_counter: Counter[str] = Counter()
        self.lock = threading.Lock()
        self.total_requests = 0
        self._stop = threading.Event()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def start(self):
        try:
            self.sock.bind((self.host, self.port))
        except PermissionError:
            sys.exit(
                f"Permission denied binding to {self.host}:{self.port}. "
                "Try running with sudo, or pass --port with a value > 1024 for testing."
            )

        print(f"Listening for DNS requests on {self.host}:{self.port} "
              f"(forwarding to {self.upstream}:{self.upstream_port})")

        dumper = threading.Thread(target=self._dump_loop, daemon=True)
        dumper.start()

        try:
            while not self._stop.is_set():
                try:
                    data, addr = self.sock.recvfrom(4096)
                except OSError:
                    break
                threading.Thread(
                    target=self._handle_query, args=(data, addr), daemon=True
                ).start()
        finally:
            self._dump(final=True)

    def stop(self):
        self._stop.set()
        self.sock.close()

    def _handle_query(self, data: bytes, addr: tuple[str, int]):
        src_ip = addr[0]
        parsed = parse_query(data)
        qname = parsed[0] if parsed else "<unparseable>"
        qtype = QTYPES.get(parsed[1], str(parsed[1])) if parsed else "?"

        with self.lock:
            self.url_counter[qname] += 1
            self.ip_counter[src_ip] += 1
            self.total_requests += 1

        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {src_ip:>15}  {qtype:<6} {qname}")

        response = self._forward(data)
        if response is not None:
            try:
                self.sock.sendto(response, addr)
            except OSError:
                pass

    def _forward(self, data: bytes) -> bytes | None:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as upstream_sock:
                upstream_sock.settimeout(5)
                upstream_sock.sendto(data, (self.upstream, self.upstream_port))
                response, _ = upstream_sock.recvfrom(4096)
                return response
        except OSError:
            return None

    def _dump_loop(self):
        while not self._stop.wait(self.dump_interval):
            self._dump()

    def _dump(self, final: bool = False):
        with self.lock:
            state = {
                "generated_at": datetime.now().isoformat(),
                "total_requests": self.total_requests,
                "urls": dict(self.url_counter.most_common()),
                "source_ips": dict(self.ip_counter.most_common()),
            }
            top_urls = self.url_counter.most_common(self.top)
            top_ips = self.ip_counter.most_common(self.top)
            total = self.total_requests

        self.dump_file.parent.mkdir(parents=True, exist_ok=True)
        self.dump_file.write_text(json.dumps(state, indent=2))

        label = "FINAL SUMMARY" if final else "SUMMARY"
        print(f"\n=== {label} ({total} requests total, dumped to {self.dump_file}) ===")
        print(f"-- Top {self.top} domains --")
        for name, count in top_urls:
            print(f"  {count:>6}  {name}")
        print(f"-- Top {self.top} source IPs --")
        for ip, count in top_ips:
            print(f"  {count:>6}  {ip}")
        print()


def main():
    parser = argparse.ArgumentParser(description="DNS request logger/proxy")
    parser.add_argument("--host", default="0.0.0.0", help="Address to listen on")
    parser.add_argument("--port", type=int, default=53, help="Port to listen on")
    parser.add_argument("--upstream", default="1.1.1.1", help="Upstream DNS server to forward queries to")
    parser.add_argument("--upstream-port", type=int, default=53, help="Upstream DNS server port")
    parser.add_argument(
        "--dump-file",
        default=str(Path(__file__).parent / "dns_stats.json"),
        help="File to periodically dump counters to",
    )
    parser.add_argument(
        "--dump-interval", type=float, default=30.0,
        help="Seconds between dumps to file and on-screen summaries",
    )
    parser.add_argument("--top", type=int, default=10, help="Number of top entries to show in summaries")
    args = parser.parse_args()

    server = DNSLoggerServer(
        args.host, args.port, args.upstream, args.upstream_port,
        args.dump_file, args.dump_interval, args.top,
    )

    def handle_signal(signum, frame):
        print("\nShutting down...")
        server.stop()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    server.start()


if __name__ == "__main__":
    main()

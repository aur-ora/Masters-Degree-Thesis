#!/usr/bin/env python
import os
import sys, time
from scapy.all import sniff, sendp, get_if_list, get_if_hwaddr, get_if_raw_hwaddr, get_if_addr
from scapy.all import Ether, IP, UDP, DHCP, BOOTP, TCP, Raw

def send_dhcp(iface):
    fam, hw = get_if_raw_hwaddr(iface) # returns family and hardware address of the interface
    print("Sending a DHCP packet on interface %s" % (iface))
    pkt = Ether(src = get_if_hwaddr(iface), dst = 'ff:ff:ff:ff:ff:ff')
    # Assembling a DHCP discover message
    pkt = pkt / IP(src = get_if_addr(iface), dst='255.255.255.255') / UDP(dport=67, sport=68) / BOOTP(op = 1, chaddr = hw) / DHCP(options = [('message-type','request'), ('end')])
    sendp(pkt, iface = iface, verbose = False) # sendp works at layer 2
    print("Packet was sent")

# def handle_pkt(pkt):
#     if IP in pkt and pkt[IP].src == "10.0.1.2":
#         if "DHCP options" in pkt:
#             os.system("sudo ip addr add " + pkt["DHCP options"].options[-1].decode() + "/24 dev eth0")
#             print("IP " + str(pkt[IP].dst) + " was assigned")
#     exit(1)

def main():
    ifaces = list(filter(lambda i: 'eth' in i, os.listdir('/sys/class/net/')))
    iface = ifaces[0]
    if get_if_addr(iface) == "0.0.0.0":
    	send_dhcp(iface)
    	# print("Listening for a response from the DHCP server on %s" % iface)
    	# sys.stdout.flush()
    	# sniff(iface = iface, filter = "inbound", prn = lambda x: handle_pkt(x))
    else:
        send_dhcp(iface)
        print("Host has already an IP")

if __name__ == '__main__':
	main()

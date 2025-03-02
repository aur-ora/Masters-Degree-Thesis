#!/usr/bin/env python
import sys
import os

from scapy.all import sniff, sendp, get_if_list, get_if_hwaddr, get_if_raw_hwaddr, get_if_addr
from scapy.all import Ether, IP, UDP, DHCP, BOOTP, TCP, Raw, ARP, ICMP

import ipaddress, time

# initialize a pool of IPv4 Address
ip_pool = []
ip_pool.append(ipaddress.IPv4Address("10.0.1.1"))
for i in range(0, 10):
    ip_pool.append(ip_pool[i] + 1)
ip_pool.remove(ipaddress.IPv4Address("10.0.1.2"))

# def assign_ip(pkt):
#     ifaces = list(filter(lambda i: 'eth' in i, os.listdir('/sys/class/net/')))
#     iface = ifaces[0]
#     fam, hw = get_if_raw_hwaddr(iface)
#     client_hw_addr = pkt[Ether].src
#     time.sleep(3)
#     print("Assigning IP...")
#
#     pkt[IP].src = ip_pool[0]
#     ip_pool.remove(pkt[IP].src)
#     client_ip_addr = str(pkt[IP].src)
#
#     rpkt = Ether(src = get_if_hwaddr(iface), dst =client_hw_addr)
#     rpkt = rpkt / IP(src=get_if_addr(iface), dst=client_ip_addr)
#     rpkt = rpkt / UDP(dport = 68, sport = 67) / BOOTP(op = 2, chaddr = hw)
#     rpkt = rpkt / DHCP(options = [('message-type', 'ack'), ('end')])
#     rpkt = rpkt / Raw(load=str(client_ip_addr))
#     sendp(rpkt, iface=iface, verbose=False)
#     time.sleep(1)
#     # exit(1) # needs to be commented if we run the first version

def handle_pkt(pkt):
    if UDP in pkt and pkt[UDP].dport == 67:
        if BOOTP in pkt and pkt[BOOTP].op == 1:
            if IP in pkt and BOOTP in pkt and pkt[IP].src == "0.0.0.0":
                print("Got a DHCP packet from " + str(pkt[Ether].src))
                # if pkt[Ether].src == "00:00:00:00:01:01":
                #     print("Got a DHCP packet from " + str(pkt[Ether].src))
                # else:
                #     print("Got a DHCP packet from " + "00:00:00:00:01" + str(pkt[BOOTP].chaddr.decode()).replace(r"\x", ":"))
            	# assign_ip(pkt) # to comment if we use the first version
        # elif BOOTP in pkt and pkt[BOOTP].op == 7:
        #     ip_pool.append(pkt[IP].src)
        #     print("An IP was freed")
    #
    # else:
    # 	if ICMP not in pkt and IP in pkt and pkt[IP].src != "10.0.1.2":
    #         print("Got a packet from " + str(pkt[IP].src))
    #         exit(1)

def main():
    ifaces = list(filter(lambda i: 'eth' in i, os.listdir('/sys/class/net/')))
    iface = ifaces[0]
    print("sniffing on %s" % iface)
    sys.stdout.flush()
    sniff(iface = iface, filter = "inbound", prn = lambda x: handle_pkt(x))
    # sniff function passes the packet object as the one arg into prn: func

if __name__ == '__main__':
	main()

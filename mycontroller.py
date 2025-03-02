#!/usr/bin/env python3
import argparse, json
import os, sys, time, ipaddress, grpc
from scapy.all import *
from threading import Thread
from time import sleep

from multiprocessing import Process

# Import P4Runtime lib from parent utils dir
sys.path.insert(0, 'utils/')
import p4runtime_lib.bmv2
import p4runtime_lib.helper
from p4runtime_lib.switch import ShutdownAllSwitchConnections

# initializing list that will contain the keys of the tables
# dhcp_requests_keys = []
trusted_host_keys = []

topology = json.load(open("topology.json", "r"))
hosts = topology['hosts'] # hosts that can connect to the network
switches = topology['switches'] # switches in the network
links = {}
for l in topology['links']:
    if l[0][0] != "s":
        links[l[1].replace("p", "eth")] = l[0].replace("p", "eth")
    else:
        links[l[1].replace("p", "eth")] = l[0].replace("p", "eth")
        links[l[0].replace("p", "eth")] = l[1].replace("p", "eth")

# dictionary in which we keep the port and mac/host mapping
port_mac = {}

# dictionary that keeps the max number of hosts a port can have
port_ndevices_max = {}

# def writeDHCPRules(p4info_helper, sw, dst_eth_addr, src_eth_addr, dst_port):
#     """
#     Installs one rule:
#         if it's a DHCP packet, add in dhcp_requests and follow action fwd_pkt_server
#     :param p4info_helper: the P4Info helper
#     :param sw: the P4 switch
#     :param dst_eth_addr: the ethernet address of the destination of the packet
#     :param src_eth_addr: the ethernet address of the source of the packet
#     :param dst_port: the destination port
#     """
#     # DHCP Packets Rule
#     table_entry = p4info_helper.buildTableEntry(
#         table_name="IngressProcess.dhcp_requests",
#         match_fields={
#             "hdr.ethernet.srcAddr": (src_eth_addr, 48)
#             },
#         action_name="IngressProcess.fwd_pkt_server",
#         action_params={
#             "dstAddr": dst_eth_addr,
#             "port": dst_port
#             })
#     sw.WriteTableEntry(table_entry)
#     dhcp_requests_keys.append(str(src_eth_addr))
#     print("Installed DHCP packets rule on %s" % sw.name + " for %s" % src_eth_addr)

# def writeNonDHCPRules(p4info_helper, sw, dst_ip_addr, src_ip_addr, dst_port):
#     """
#     Installs one rule:
#         if it's not a DHCP packet, the match needs to be in trusted_host
#     :param p4info_helper: the P4Info helper
#     :param sw: the P4 switch
#     :param dst_ip_addr: the IP address of the destination of the packet
#     :param src_ip_addr: the IP address of the source of the packet
#     :param dst_port: the destination port
#     """
#     # Non-DHCP Packets Rule
#     table_entry = p4info_helper.buildTableEntry(
#         table_name="IngressProcess.trusted_host",
#         match_fields={
#             "hdr.ipv4.srcAddr": (src_ip_addr, 32),
#             "hdr.ipv4.dstAddr": (dst_ip_addr, 32)
#             },
#         action_name="IngressProcess.send_to_controller",
#         action_params={
#             "dstAddr": dst_ip_addr,
#             "port": dst_port
#             })
#     sw.WriteTableEntry(table_entry)
#     trusted_host_keys.append((str(src_ip_addr), str(dst_ip_addr)))
#     print("Installed non-DHCP packets rule on %s" % sw.name + " for %s" % src_ip_addr)

# def dhcp_server(pkt, s1, p4info_helper, port_ndevices_max):
#     port_pkt = pkt.sniffed_on
#     # if (str(pkt[IP].src), str(pkt[IP].dst)) not in trusted_host_keys:
#     #     writeNonDHCPRules(p4info_helper, sw=s1, dst_ip_addr=pkt[IP].dst, src_ip_addr=pkt[IP].src, dst_port=int([i[-1] for i in port_mac.keys() if pkt[Ether].dst in port_mac[i]][0]))
#     # iface = "s1-eth" + str(pkt[IP].dst)[-1]
#     iface = str([i for i in port_mac.keys() if pkt[Ether].dst in port_mac[i]][0])
#     print("Transferring from the DHCP server to " + str(pkt[Ether].dst))
#     sendp(pkt, iface=iface, verbose=False)

# sending DHCP packet to the DHCP server
def dhcp_packet(pkt, s1, p4info_helper, client_hw_addr):
    if IP in pkt and pkt[IP].src == "0.0.0.0":
        print("Sending the DHCP packet to the DHCP server")
        sendp(pkt, iface="s1-eth2", verbose = False) # sending the packet to the DHCP server
    # else:
    #     print("Host has already the following IP " + str(pkt[IP].src))

# after timeout we restore the port
def free_port(port_ndevices, port_ndevices_max, port_pkt):
    port_ndevices[port_pkt] = port_ndevices_max[port_pkt]

# handleing of DHCP and non-DHCP packets incoming on the switch s1
def handle_pkt(pkt, s1, p4info_helper, port_ndevices, port_ndevices_max):
    if BOOTP in pkt and pkt[BOOTP].op == 1:
        port_pkt = pkt.sniffed_on
        client_hw_addr = pkt[Ether].src
        host_connected = len(port_mac[port_pkt])

        if port_ndevices[port_pkt] > 0:
            print("We received a DHCP packet on port " + str(port_pkt))
            # if the number of devices connected to that port is the max there can be
            if port_ndevices_max[port_pkt] == host_connected:
                port_mac[port_pkt][0] = client_hw_addr # that means that there is a new device connected
            elif port_ndevices_max[port_pkt] > host_connected: # if there can connected still connect other hosts
                port_mac[port_pkt].append(client_hw_addr) # add it to the mac address table
            dhcp_packet(pkt, s1, p4info_helper, client_hw_addr) # we call the function that sends the DHCP packet to the server
            port_ndevices[port_pkt] -= 1
        else:
            if port_ndevices[port_pkt] == 0:
                print("Port " + str(port_pkt) + " is blocked")
                port_ndevices[port_pkt] = -1
                t = threading.Timer(10, free_port, [port_ndevices, port_ndevices_max, port_pkt])
                t.start()

    # elif BOOTP in pkt and pkt[BOOTP].op == 2:
    #     print("Servers response")
    #     dhcp_server(pkt, s1, p4info_helper, port_ndevices_max)

# we get the number of devices connected to a certain port, it gets saved in port_ndevices_max
def get_devices(ifaces):
    sw = {}
    for iface in ifaces:
        port_mac[iface] = []
        value = links[iface]
        if value[0] == "h":
            port_ndevices_max[iface] = 1
        else:
            sw[iface] = []
            for k,v in links.items():
                if k.startswith(value[:2]) and k != value:
                    if v.startswith("h"): sw[iface].append(v)
                    else: sw[iface].append(str(k))
        print(iface, end=' ~ ')

    for k, v in sw.items():
        x = 0
        for i in v:
            if i.startswith("h"): x += 1
            else:
                value = sw[i].copy()
                while value != []:
                    temp = value.copy()
                    for y in temp:
                        if y.startswith("h"):
                            x += 1
                            value.remove(y)
                        else: value = sw[y].copy()
        port_ndevices_max[k] = x

def main(p4info_file_path, bmv2_file_path):
    # Instantiate a P4Runtime helper from the p4info file
    p4info_helper = p4runtime_lib.helper.P4InfoHelper(p4info_file_path)

    try:
        # Create a switch connection object for all the switches; this is backed by a P4Runtime gRPC connection. Also, dump all P4Runtime messages sent to switch to given txt files.
        for s in switches:
            switch = p4runtime_lib.bmv2.Bmv2SwitchConnection(
                name=s,
                address='127.0.0.1:5005' + s[1],
                device_id=int(s[1]) - 1,
                proto_dump_file='logs/s' + s[1] + '-p4runtime-requests.txt')

            # Send master arbitration update message to establish this controller as master (required by P4Runtime before performing any other write operation)
            switch.MasterArbitrationUpdate()

            # Install the P4 program on the switch
            switch.SetForwardingPipelineConfig(p4info=p4info_helper.p4info, bmv2_json_file_path=bmv2_file_path)
            print("Installed P4 Program using SetForwardingPipelineConfig on s" + s[1])

        ifaces = sorted(list(filter(lambda i: '-eth' in i, os.listdir('/sys/class/net/'))))
        print("\nSniffing on:")
        get_devices(ifaces)
        print("\n")

        # port_ndevices_max is the table of matching port and devices that can connect --> we need this to know the max devices possible
        port_ndevices = port_ndevices_max.copy()
        # sys.stdout.flush()
        sniff(iface=ifaces, filter = "inbound and udp and (port 67 or 68)",
        prn = lambda x: handle_pkt(x, switch, p4info_helper, port_ndevices, port_ndevices_max))


    except KeyboardInterrupt:
        print(" Shutting down.")
    except grpc.RpcError as e:
        printGrpcError(e)

    ShutdownAllSwitchConnections()

def printGrpcError(e):
    print("gRPC Error:", e.details(), end=' ')
    status_code = e.code()
    print("(%s)" % status_code.name, end=' ')
    traceback = sys.exc_info()[2]
    print("[%s:%d]" % (traceback.tb_frame.f_code.co_filename, traceback.tb_lineno))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='P4Runtime Controller')
    parser.add_argument('--p4info', help='p4info proto in text format from p4c', type=str, action="store", required=False, default='./build/dhcp-mitigate.p4.p4info.txt')
    parser.add_argument('--bmv2-json', help='BMv2 JSON file from p4c',type=str, action="store", required=False, default='./build/dhcp-mitigate.json')
    args = parser.parse_args()

    if not os.path.exists(args.p4info):
        parser.print_help()
        print("\np4info file not found: %s\nHave you run 'make'?" % args.p4info)
        parser.exit(1)
    if not os.path.exists(args.bmv2_json):
        parser.print_help()
        print("\nBMv2 JSON file not found: %s\nHave you run 'make'?" % args.bmv2_json)
        parser.exit(1)
    main(args.p4info, args.bmv2_json)

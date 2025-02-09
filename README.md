# Exploiting network programmability to mitigate DHCP starvation attacks
The project was made as a master's thesis. It is based on a six-month internship. \
The topic of the project is the exploitation of network programmability to mitigate known attacks.
\
The solution needs to be run after the P4Tutorial VM (https://github.com/p4lang/tutorials) has been downloaded and installed correctly. \
\
The main objective of the project is to avoid Denial-of-Service attacks, such as DHCP starvation attacks when managing a network. \
The control plane serves as the main area of interest because it is where all features are implemented and where the most important defences against DHCP attacks are employed.

<p align="center">
    <img width="500" src="https://github.com/aur-ora/Masters-Degree-Thesis/blob/main/topo.png">
</p>

The **utils** folder, taken from the repository mentioned above, is the folder that contains the main files needed to run the project. \
\
The **mycontroller.py** file is the main file in which the controller is defined with its functionalities. \
\
The **topology.json** file contains the configuration of the topology used.\
\
The **dhcp-packet.py**, **malicious-packet.py** and **server-response.py** files are the Python scripts used to demonstrate the functioning of the implementation.


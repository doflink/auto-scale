# Scaling mechanism for Open-Stack
Auto-scaling mechanism for applications deployed on Open-Stack-based cloud

###What is this repository for? ###
* Auto-scaling mechanism for LEADS project.
* [Wiki](https://github.com/leads-project/auto-scale/wiki)

### How to run? ###
* Deploy [UniMon](https://github.com/leads-project/unimon) to monitor all VMs on clouds
* Adjust the parameters in setting.json (where the redis server for Unimon is running) and authentication (of your openstack infrastructure) in infrastructure.auth
* Run $python vertical_scaling.py

### Dependencies ###
* Python 2.x with novaclient.v1_1, redis, shutil package

### Contact? ###
* Do Quoc Le (SE Group TU Dresden): do@se.inf.tu-dresden.de 



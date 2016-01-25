Scaling mechanism for Open-Stack
==============
Auto-scaling mechanism for applications deployed on Open-Stack-based cloud
* [Wiki](https://github.com/leads-project/auto-scale/wiki)

# Dependencies #
* Python 2.x with ($ pip install python-novaclient==2.10.0 redis==2.10.5)
* OpenStack havanna installation or newer

# Configuration #
* Adjust the parameters in `setting.json` (where the redis server for Unimon is running) and authentication (of your openstack infrastructure) in infrastructure.auth

# How to run the code #
* Deploy [UniMon](https://github.com/leads-project/unimon) to monitor all VMs on clouds
* Run `$python vertical_scaling.py`

# Contact #
* Do Le Quoc (SE Group TU Dresden): do@se.inf.tu-dresden.de 



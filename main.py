from datacenter import Datacenter
from config import Config
from datacenter import Datacenter

def generate_datacenters(datacenter_num):
    datacenter_list=[]
    for i in range(datacenter_num):
        datacenter_list.append(Datacenter(i))
    for i in range(datacenter_num):
        datacenter_list[i].set_datacenters(datacenter_list)
    return datacenter_list

if __name__ == '__main__':
    # initialize configurations
    conf=Config()
    # initialize datacenters, each element is a Datacenter type item
    datacenters=generate_datacenters(conf.datacenter_num)
    # datacenter with id 0 make 20 random queries with lookup method EPI
    queries = datacenters[0].make_queries(20, "EPI")



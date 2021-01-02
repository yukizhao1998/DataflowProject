from datacenter import Datacenter
from config import Config
from datacenter import Datacenter
import random
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
    # make queries, choose datacenters randomly
    cnt = 0
    with open(conf.load_query_path, 'r') as file:
        while True:
            if cnt == 10:
                break
            line = file.readline()
            cnt += 1
            if line:
                query = line.strip("\n")
                datacenter_id = random.randint(0, conf.datacenter_num - 1)
                datacenters[datacenter_id].make_query(query, "epi")
            else:
                break
    #queries = datacenters[0].make_queries(20, "EPI")



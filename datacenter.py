from bloomfilter import BloomFilter
from config import Config
import random
class Datacenter:
    def __init__(self, id):
        # id: from 0 to 16
        self.id=id
        self.conf=Config()
        self.datacenters=[]
        self.datastore=[]
        self.queries=[]
        self.load_datastore(self.conf.load_datastore_path+str(self.id))
        self.load_query(self.conf.load_query_path+str(self.id))
        self.bf=BloomFilter(len(self.datastore), self.conf.bf_fprate)
        self.insert_bf()

    # load datastore into datastore list
    def load_datastore(self, load_datastore_path):
        print("Datacenter %d loading datastore..." % self.id)
        with open(load_datastore_path, 'r') as file:
            while True:
                line=file.readline()
                if line:
                    self.datastore.append(line)
                else:
                    break

    # load query into queries list
    def load_query(self, load_query_path):
        print("Datacenter %d loading queries..." % self.id)
        with open(load_query_path, 'r') as file:
            while True:
                line = file.readline()
                if line:
                    self.queries.append(line)
                else:
                    break

    #set_datacenters
    def set_datacenters(self, datacenters):
        self.datacenters=datacenters

    #insert items in datastore into bloomfilter
    def insert_bf(self):
        for item in self.datastore:
            self.bf.add(item)

    # lookup an item in bloomfilter, return True or False
    def lookup_in_bloomfilter(self, item):
        return self.bf.is_member(item)

    # lookup an item in datacenter, false positive rate == 0, return True or False
    def lookup_groundtruth(self, item):
        return item in self.datastore

    # EPI lookup method, lookup every datacenters
    def epi(self, query):
        cost = 0
        positive_datacenters=[]
        groundtruth_datacenters=[]
        # lookup every datacenter, datacenter is type Datacenter
        for datacenter in self.datacenters:
            cost+=self.cal_cost(datacenter.id)
            if datacenter.lookup_in_bloomfilter(query):
                positive_datacenters.append(datacenter.id)
            if datacenter.lookup_groundtruth(query):
                groundtruth_datacenters.append(datacenter.id)
        print("Datacenter %d queries %s, %d datacenters returns positive result, %d datacenters really have records."
              %(self.id, query, len(positive_datacenters), len(groundtruth_datacenters)))

    # TODO
    # make the first query_number queries
    # can add lookup methods here
    def make_queries(self, query_number, method):
        sample_queries = random.sample(self.queries, query_number)
        for query in sample_queries:
            if method=='EPI':
                self.epi(query)

    # TODO
    # lookup the cost from this datastore to another
    def cal_cost(self, datacenter_id):
        return 1

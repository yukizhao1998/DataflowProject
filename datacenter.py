from bloomfilter import BloomFilter
from config import Config
import random
import numpy as np
import functools

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
        self.cost_matrix=self.conf.cost_matrix
        self.miss_penalty=self.conf.punishment

    # load datastore into datastore list
    def load_datastore(self, load_datastore_path):
        print("Datacenter %d loading datastore..." % self.id)
        with open(load_datastore_path, 'r') as file:
            while True:
                line=file.readline()
                if line:
                    self.datastore.append(line.strip('\n'))
                else:
                    break

    # load query into queries list
    def load_query(self, load_query_path):
        print("Datacenter %d loading queries..." % self.id)
        with open(load_query_path, 'r') as file:
            while True:
                line = file.readline()
                if line:
                    self.queries.append(line.strip('\n'))
                else:
                    break
    
    # cmp used to sort the datastores based on their cost from this datastore
    def cmp(self, x1, x2):
        return self.cost_matrix[self.id][x1.id] < self.cost_matrix[self.id][x2.id]

    #set_datacenters
    def set_datacenters(self, datacenters):
        self.datacenters=datacenters
        self.datacenters.sort(key=functools.cmp_to_key(self.cmp))

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

    # Lookup with perfect indicator
    def perfect_indicator(self, query):
        for datacenter in self.datacenters:
            if datacenter.lookup_groundtruth(query):
                return self.cost_matrix[self.id][datacenter.id]
        return self.miss_penalty

    # CPI lookup method, lookup cheapest positive datacenters
    def cpi(self, query):
        cost = 0
        for datacenter in self.datacenters:
            if datacenter.lookup_in_bloomfilter(query):
                cost += self.cal_cost(datacenter.id)
                if datacenter.lookup_groundtruth(query):
                    return cost
                else:
                    return cost + self.miss_penalty
        return self.miss_penalty

    # EPI lookup method, lookup every positive datacenters
    def epi(self, query):
        cost = 0
        miss = self.miss_penalty
        #positive_datacenters=[]
        #groundtruth_datacenters=[]
        # lookup every datacenter, datacenter is type Datacenter
        for datacenter in self.datacenters:
            if datacenter.lookup_in_bloomfilter(query):
                #positive_datacenters.append(datacenter.id)
                cost+=self.cal_cost(datacenter.id)
                if datacenter.lookup_groundtruth(query):
                    miss = 0
                    #groundtruth_datacenters.append(datacenter.id)
        #print("Datacenter %d queries %s, %d datacenters returns positive result, %d datacenters really have records."
        #      %(self.id, query, len(positive_datacenters), len(groundtruth_datacenters)))
        return cost+miss

    # TODO
    # make the first query_number queries
    # can add lookup methods here
    def make_queries(self, query_number, method):
        sample_queries = random.sample(self.queries, query_number)
        for query in sample_queries:
            if method == 'EPI':
                self.epi(query)

    # test all queries
    def test(self, method):
        total_cost = 0
        count = 0
        query_num = len(self.queries)
        for query in self.queries:
            if count % 1000 == 0:
                print("%d / %d completed, with total cost %d."%(count, query_num, total_cost))
            count += 1
            if method == 'P_I':
                total_cost += self.perfect_indicator(query)
            elif method == 'epi':
                total_cost += self.epi(query)
            elif method == 'cpi':
                total_cost += self.cpi(query)
        print("Datacenter %d: test %s completed with total cost %d"%(self.id, method, total_cost))
        return total_cost


    # lookup the cost from this datastore to another
    def cal_cost(self, datacenter_id):
        return self.cost_matrix[self.id][datacenter_id]

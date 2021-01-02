from bloomfilter import BloomFilter
from config import Config
import random
import numpy as np
import functools
import collections
from probables import (BloomFilter)
from probables import (CountingBloomFilter)

class LRUCache(collections.OrderedDict):

    def __init__(self):
        conf = Config()
        self.size = conf.cache_size
        self.cache = collections.OrderedDict()
 
    def get(self, key):
        if key in self.cache.keys():
            value = self.cache.pop(key)
            self.cache[key] = value
            return True
        else:
            value = None
            return False
 
    def put(self, key):
        if key in self.cache.keys():
            self.cache.pop(key)
            self.cache[key] = 0
        elif self.size == len(self.cache):
            item = self.cache.popitem(last=False)
            self.cache[key] = 0
            return True, item
        else:
            self.cache[key] = 0
        return False, None

class Datacenter:
    def __init__(self, id):
        # id: from 0 to 16
        self.id=id
        self.conf=Config()
        self.datacenters=[]
        self.queries=[]
        self.lrucache = LRUCache()
        if self.conf.filter_type == "BloomFilter":
            self.filter = BloomFilter(est_elements = self.conf.cache_size, false_positive_rate=self.conf.fprate)
        if self.conf.filter_type == "CountingBloomFilter":
            self.filter = CountingBloomFilter(est_elements = self.conf.cache_size, false_positive_rate=self.conf.fprate)
        self.load_datastore(self.conf.load_datastore_path+str(self.id))
        #self.load_query(self.conf.load_query_path+str(self.id))
        # can define multiple filters here
        self.init_filter()
        self.cost_matrix=self.conf.cost_matrix
        self.miss_penalty=self.conf.miss_penalty


    # load datastore into datastore list
    def load_datastore(self, load_datastore_path):
        print("Datacenter %d loading datastore..." % self.id)
        with open(load_datastore_path, 'r') as file:
            while True:
                line=file.readline()
                if line:
                    self.lrucache.put(line.strip('\n'))
                else:
                    break

    # load query into queries list
    '''
    def load_query(self, load_query_path):
        print("Datacenter %d loading queries..." % self.id)
        with open(load_query_path, 'r') as file:
            while True:
                line = file.readline()
                if line:
                    self.queries.append(line.strip('\n'))
                else:
                    break
    '''
    
    # cmp used to sort the datastores based on their cost from this datastore
    def cmp(self, x1, x2):
        return self.cost_matrix[self.id][x1.id] < self.cost_matrix[self.id][x2.id]

    #set_datacenters
    def set_datacenters(self, datacenters):
        self.datacenters=datacenters
        self.datacenters.sort(key=functools.cmp_to_key(self.cmp))

    #insert items in datastore into filter
    def init_filter(self):
        for item in self.lrucache.cache.keys():
            #print(item)
            self.filter.add(item)

    #insert an item into filter
    def insert_filter(self, item):
        self.filter.add(item)

    # lookup an item in filter, return True or False
    def lookup_in_filter(self, item):
        self.lrucache.get(item)
        return self.filter.check(item)

    # delete an item in filter
    def delete_filter_item(self, item):
        if self.conf.filter_type == "BloomFilter":
            return
        else:
            self.filter.remove(item)

    # lookup an item in datacenter, false positive rate == 0, return True or False
    def lookup_groundtruth(self, item):
        return self.lrucache.get(item)

    # insert an item into datacenter
    def insert_datacenter(self, item):
        kick, kicked_item = self.lrucache.put(item)
        if kick:
            self.delete_filter_item(kicked_item)
        self.insert_filter(item)

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
        positive_datacenters=[]
        groundtruth_datacenters=[]
        # lookup every datacenter, datacenter is type Datacenter
        for datacenter in self.datacenters:
            if datacenter.lookup_in_filter(query):
                positive_datacenters.append(datacenter.id)
                cost+=self.cal_cost(datacenter.id)
                if datacenter.lookup_groundtruth(query):
                    miss = 0
                    groundtruth_datacenters.append(datacenter.id)
        print("Datacenter %d queries %s, %d datacenters returns positive result, %d datacenters really have records."
              %(self.id, query, len(positive_datacenters), len(groundtruth_datacenters)))
        return cost+miss

    # TODO
    # make the first query_number queries
    # can add lookup methods here
    def make_query(self, query, method):
        total_cost = 0
        total_cost += self.conf.cache_cost
        if not self.lrucache.get(query):
            #total_cost += self.conf.cache_cost
            past_cost = total_cost
            if method == 'P_I':
                total_cost += self.perfect_indicator(query)
            elif method == 'epi':
                total_cost += self.epi(query)
            elif method == 'cpi':
                total_cost += self.cpi(query)
            if total_cost - past_cost < self.miss_penalty: #don't know what it means
                self.insert_datacenter(query)

    # test all queries
    def test(self, method):
        total_cost = 0
        count = 0
        query_num = len(self.queries)
        for query in self.queries:
            if count % 1000 == 0:
                print("%d / %d completed, with total cost %d."%(count, query_num, total_cost))
            count += 1
            if self.lrucache.get() is False:
                total_cost += self.conf.cache_cost
                past_cost = total_cost
                if method == 'P_I':
                    total_cost += self.perfect_indicator(query)
                elif method == 'epi':
                    total_cost += self.epi(query)
                elif method == 'cpi':
                    total_cost += self.cpi(query)
                if total_cost - past_cost < self.miss_penalty:
                    self.lrucache.put(query)

        print("Datacenter %d: test %s completed with total cost %d"%(self.id, method, total_cost))
        return total_cost


    # lookup the cost from this datastore to another
    def cal_cost(self, datacenter_id):
        return self.cost_matrix[self.id][datacenter_id]

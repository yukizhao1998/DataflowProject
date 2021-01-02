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
    query_cnt = [0] * 17
    miss_cnt = [0] * 17
    missind_ratio = [0] * 17
    def __init__(self, id):
        # id: from 0 to 16
        self.id=id
        self.conf=Config()
        self.datacenters=[]
        self.datastore=[]
        self.queries=[]
        self.lrucache = LRUCache()
        if self.conf.filter_type == "BloomFilter":
            self.filter = BloomFilter(est_elements = self.conf.cache_size, false_positive_rate=self.conf.fprate)
        if self.conf.filter_type == "CountingBloomFilter":
            self.filter = CountingBloomFilter(est_elements = self.conf.cache_size, false_positive_rate=self.conf.fprate)
        self.load_datastore(self.conf.load_datastore_path+str(self.id))
        self.init_filter()
        self.cost_matrix = self.conf.cost_matrix
        self.miss_penalty = self.conf.miss_penalty
        self.update_epoch = self.conf.update_epoch

    # load datastore into datastore list
    def load_datastore(self, load_datastore_path):
        print("Datacenter %d loading datastore..." % self.id)
        with open(load_datastore_path, 'r', encoding='utf-8') as file:
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
                return self.cost_matrix[self.id][datacenter.id], 0
        return 0, self.miss_penalty

    # CPI lookup method, lookup cheapest positive datacenters
    def cpi(self, query):
        cost = 0
        for datacenter in self.datacenters:
            if datacenter.lookup_in_filter(query):
                cost += self.cal_cost(datacenter.id)
                if datacenter.lookup_groundtruth(query):
                    return cost, 0
                else:
                    return cost, self.miss_penalty
        return 0, self.miss_penalty

    # EPI lookup method, lookup every positive datacenters
    def epi(self, query):
        cost = 0
        miss = self.miss_penalty
        for datacenter in self.datacenters:
            if datacenter.lookup_in_filter(query):
                #positive_datacenters.append(datacenter.id)
                cost+=self.cal_cost(datacenter.id)
                if datacenter.lookup_groundtruth(query):
                    miss = 0
        return cost, miss

    # cmp_p used to sort the datastores based on their misindictation ratio
    def cmp_mi(self, x1, x2):
        return Datacenter.missind_ratio[x1.id] < Datacenter.missind_ratio[x2.id]

    # DSpot loopup method
    def DSpot(self, query):
        miss = self.miss_penalty
        positive_datacenters = []
        positive_costs = []
        for datacenter in self.datacenters:
            if datacenter.lookup_in_filter(query):
                positive_datacenters.append(datacenter)
                positive_costs.append(self.cal_cost(datacenter.id))
        if len(positive_datacenters) == 0:
            return 0, miss
        
        # cal Lx
        positive_costs.sort()
        for i in range(1, len(positive_costs)):
            positive_costs[i] = positive_costs[i] + positive_costs[i - 1]
        
        c_min = miss * 2
        cost = 0
        p_miss = 1.0
        positive_datacenters.sort(key=functools.cmp_to_key(self.cmp_mi))
        for i in range(len(positive_datacenters)):
            p_miss *= Datacenter.missind_ratio[positive_datacenters[i].id]
            temp_c = positive_costs[i] + p_miss * self.miss_penalty
            if temp_c >= c_min:
                return cost, miss
            else:
                Datacenter.query_cnt[positive_datacenters[i].id] += 1
                cost += self.cal_cost(positive_datacenters[i].id)
                if positive_datacenters[i].lookup_groundtruth(query):
                    miss = 0
                else:
                    Datacenter.miss_cnt[positive_datacenters[i].id] += 1
                if Datacenter.query_cnt[positive_datacenters[i].id] <= self.update_epoch:
                    Datacenter.missind_ratio[positive_datacenters[i].id] = \
                        float(Datacenter.miss_cnt[positive_datacenters[i].id]) / float(Datacenter.query_cnt[positive_datacenters[i].id])
                elif (Datacenter.query_cnt[positive_datacenters[i].id] % self.update_epoch == 0):
                    Datacenter.missind_ratio[positive_datacenters[i].id] = \
                        0.1 * float(Datacenter.miss_cnt[positive_datacenters[i].id]) / self.update_epoch +\
                        0.9 * Datacenter.missind_ratio[positive_datacenters[i].id]
                    Datacenter.miss_cnt[positive_datacenters[i].id] = 0
                    print("Datacenter %d miss ratio after %d queries: %f"%(positive_datacenters[i].id, \
                    Datacenter.query_cnt[positive_datacenters[i].id], Datacenter.missind_ratio[positive_datacenters[i].id]))
        return cost, miss


    # test all queries
    def test(self, method):
        acc_cost = 0
        miss_cost = 0
        total_cost = 0
        count = 0
        query_num = len(self.queries)
        for query in self.queries:
            if count % 1000 == 0:
                print("%d / %d completed, with cost %d, %d, %d."%(count, query_num, acc_cost, miss_cost, total_cost))
            count += 1
            if method == 'P_I':
                a, m = self.perfect_indicator(query)
            elif method == 'epi':
                a, m = self.epi(query)
            elif method == 'cpi':
                a, m = self.cpi(query)
            acc_cost += a
            miss_cost += m
            total_cost = acc_cost + miss_cost
        print("Datacenter %d: test %s completed with cost %d, %d, %d"%(self.id, method, acc_cost, miss_cost, total_cost))
        return acc_cost, miss_cost, total_cost


    # lookup the cost from this datastore to another
    def cal_cost(self, datacenter_id):
        return self.cost_matrix[self.id][datacenter_id]

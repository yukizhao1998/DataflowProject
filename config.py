class Config():
    def __init__(self):
        self.datacenter_num=17
        self.copy_number=1 # 1, 3, 5
        self.dataset="1000"
        self.load_datastore_path='./'+self.dataset+'/'+str(self.copy_number)+' copy/'
        self.load_query_path='./'+self.dataset+'/query/'
        self.bf_fprate=0.02 # bloomfilter's false positive rate
        self.punishment=100
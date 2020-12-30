# DataflowProject
A project based on Access Strategies for Network Caching

## Get Started
Put dataset files in the directory, and modify config.py. 

Dataset is generated from Wikipedia clickstream trace. We provide three datasets with various size: 1000 records, 10000 records and 10000 records. Download link: https://pan.baidu.com/s/1gjRkT1HYw8CgdwbyN-BoYg, extract code: 7p2s.

Run main.py, and test the basic EPI algorithm.

## Directories
config.py: Configurations defined here.

main.py: Run main.py to start your experiment, define your tasks here.

datacenter.py: Datacenter class, with records, a bloomfilter or other filters, a list of queries. After initialization, dataset is loaded. By calling make_queries(), you can test different lookup method. Define lookup methods here.

bloomfilter.py: BloomFilter class.

generate_data.py: Extract data from original clickstream data. Resource: https://figshare.com/articles/dataset/Wikipedia_Clickstream/1305770

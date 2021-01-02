import random
from config import Config

conf = Config()
def extract_from_dataset():
    word_dict={}
    stream=[]
    total=0
    print("reading dataset...")
    with open('2015_01_en_clickstream.tsv', 'r') as file:
        while True:
            total+=1
            if total%10000000==0:
                print("already read %d million records" % (total/10000000))
            line = file.readline()
            if line:
                list=line.split("	")
                word=list[-1]
                cnt=int(list[-3])
                if word in word_dict:
                    word_dict[word]+=cnt
                else:
                    word_dict[word]=cnt
            else:
                break

    word_list=random.sample(word_dict.keys(), int(conf.dataset))
    print("generating wordlist...")
    with open('wordlist.txt', 'w') as file:
        file.writelines(word_list)

    print("generating stream...")
    with open(conf.load_query_path, 'w') as file:
        for word in word_list:
            for i in range(word_dict[word]):
                stream.append(word)
        random.shuffle(stream)
        file.writelines(stream)
    print("%d words in database, %d words in tests"%(len(word_dict.keys()), len(stream)))

def distribute_copy(copy_num):
    file_list=[]
    for i in range(conf.datacenter_num):
        file = open('./'+conf.dataset+'/'+str(copy_num)+' copy/'+str(i), 'w')
        file_list.append(file)
    with open('wordlist.txt', 'r') as file:
        while True:
            line=file.readline()
            if line:
                samples=random.sample(range(conf.datacenter_num), copy_num)
                for ind in samples:
                    file_list[ind].write(line)
            else:
                break
    for file in file_list:
        file.close()

'''
def split_query():
    cnt = 0
    file_list = []
    for i in range(conf.datacenter_num):
        file = open('./data/query/' + str(i), 'w')
        file_list.append(file)
    with open('stream.txt', 'r') as file:
        while True:
            if cnt==10000000:
                break
            line=file.readline()
            if line:
                file_list[cnt%conf.datacenter_num].write(line)
                cnt+=1
            else:
                break
    for file in file_list:
        file.close()
'''
if __name__ == '__main__':
    extract_from_dataset()

    distribute_copy(1)
    distribute_copy(3)
    distribute_copy(5)

    #split_query()

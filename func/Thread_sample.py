import threading
import time
# def test(x,y):
#     for i in range(x,y):
#         print(i)
#
# thread1 = threading.Thread(name='t1',target=test,args=(1,10))
# thread2 = threading.Thread(name='t2',target=test,args=(11,20))
# thread1.start()
# thread2.start()
#
# class mythread(threading.Thread):
#     def run(self):
#         for i in range(1,10):
#             print(i)
# thread1 = mythread()
# thread2 = mythread()
# thread1.start()
# thread2.start()

# def test():
#     time.sleep
#     for i in range(10):
#         print(i)
# thread1 = threading.Thread(target=test,daemon=False)
# thread1.start()
# thread1.join()
# print('主线程完成了')

import time
import requests
from multiprocessing.dummy import Pool

# 自定义函数
def query(url):
    requests.get(url)

start = time.time()
for i in range(100):
    query('https://www.csdn.net/')
end = time.time()
print(f'单线程循环访问100次CSDN，耗时：{end - start}')

start = time.time()
url_list = []
for i in range(100):
    url_list.append('https://www.csdn.net/')
pool = Pool(5)
pool.map(query, url_list)
end = time.time()
print(f'5线程访问100次CSDN，耗时：{end - start}')

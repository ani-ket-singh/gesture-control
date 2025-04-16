import json
import http.client

connection = http.client.HTTPConnection("192.168.134.203", 80, timeout=5)
data = {"dev_id" : "", "state":""}

headers = {"Content-type":"application/json"}

while True:
    dat = input("Enter dev-id:")
    stat = input("Enter state : ")
    if dat == 'stop' or stat == 'stop':
        break
    data["dev_id"] = dat
    data["state"] = stat
    json_foo = json.dumps(data)
    connection.request("POST", "/handleDev", json_foo)
    response = connection.getresponse()
    print(response)
    connection.close()
# from CLIENT_INTERFACE.queue import CircularQueue
# import threading

# Qu = CircularQueue(12)

# def func1():
#     global Qu
#     i = 0
#     while(i < 20):
#         Qu.enQueue(i)
#         i+=1

# def func2():
#     global Qu
#     while not Qu.isEmpty():
#         print(f"{Qu.deQueue()}, ")

# t1 = threading.Thread(target=func1)
# t2 = threading.Thread(target=func2)


# if __name__ == 'main':
#     t1.start()

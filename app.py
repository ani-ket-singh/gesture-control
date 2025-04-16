import cv2
import numpy as np
import time
from flask import Flask, request, redirect, render_template
from flask_cors import CORS
import json
# from CLIENT_INTERFACE.queue import  CircularQueue
import queue
import http.client
import os
from tensorflow import keras
import threading

ESP_IP = "192.168.16.203"
HTTP_PORT = 80
STOP_ESP_CLIENT = False

GESTURE_CONTROL_ENABLED = False
PROBABILITY_THRESHOLD = 0.9

CASCADE_FILE = "cascade.xml"
MODEL_PATH = "test_model.h5"

GESTURE_MAP = {"0": "FIVE", 
               "1": "THUMB", 
               "2": "THUMB_MINI", 
               "3": "THUMB_MINI_FORE", 
               "4": "V"
               }

gesture_device_map=None
current_status = None
server_configs = None

with open("gesture_device_map.json") as file1:
    gesture_device_map = json.load(file1)
with open("current_status.json") as file2:
    current_status = json.load(file2)


connection = http.client.HTTPConnection(ESP_IP, HTTP_PORT, timeout=5)
model = keras.models.load_model(MODEL_PATH)


def send_data_to_ESP(req):
    global connection
    data_ = json.dumps(req)
    connection.request("POST", "/handleDev", data_ )
    res = connection.getresponse()
    connection.close()
    return res
    






############################################################### HANDLE DEVICES STATUS #################################
def change_status(dev_id):
    global current_status
    if (current_status[f'{dev_id}'] == 'OFF'):
        current_status[f'{dev_id}'] = 'ON'
    else:
        current_status[f'{dev_id}'] = 'OFF'
    #Save this to a file
    with open("current_status.json", 'w') as status_file:
        json.dump(current_status, status_file)
    
    
def get_status_to_change(dev_id):
    global current_status
    if current_status[f'{dev_id}'] == "ON":
        return "OFF"
    return "ON"
# ########################################################################################################################    

Qu = queue.Queue()

# ################################################ THEY NEED TO RUN CONTINUOSLY AS SEPARATE THREAD TO HANDLE QUEUED REQUESTS ##########################################



def handle_request_from_queue():
    global Qu
    global send_data_to_ESP
    while True:
        while not Qu.empty():
            req = Qu.get()
            print(req)
            res = send_data_to_ESP(req)
            change_status(req["dev_id"])

    # while not Qu.isEmpty():
    #     req = Qu.deQueue()
    #     print(req)
    #         #to_change = get_status_to_change(req["dev_id"])
    #         #req["state"] = to_change
    #         #json_foo = json.dumps(req)
    #     res = send_data_to_ESP(req)
    #     print(res)
    #     change_status(req["dev_id"])
            

########################################## THREAD 1 ##############################################################
t1 = threading.Thread(target=handle_request_from_queue)
#################################################################################################################
def handle_gesture():
    global t1
    global model
    global Qu
    global gesture_device_map
    #Stop current thread's execution if flag is disabled
    if not GESTURE_CONTROL_ENABLED:
        return
    #If not the keep scanning hands in the video frames
    video = cv2.VideoCapture(0)
    
    i = 0
    haar_cascade = cv2.CascadeClassifier(CASCADE_FILE)
    while video.isOpened():
        if not GESTURE_CONTROL_ENABLED:
            return
        _, frame = video.read()
        
        if (i% 20!= 0):
            i += 1
            pass
        else:
            #Get every 9th frame
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            hands = haar_cascade.detectMultiScale(frame, scaleFactor = 1.33, minNeighbors=7)
            detected_hands = hands
            if len(hands) >= 1:
                for hand in hands:
                    if (hand[2] >= 96 and hand[3] >= 128):
                        detected_hands = hand
                        break
                    else:
                        detected_hands = np.array([])
                if detected_hands.any():
                   print(detected_hands)
                   #Get hand cropped out of original image
                   hand_cropped_out = frame[detected_hands[1]:(detected_hands[1]+detected_hands[3]), detected_hands[0]:(detected_hands[0]+detected_hands[2])]
                #    cv2.imwrite(f"{i}.jpg", hand_cropped_out)
                   #Resize the image to fit to model's input shape
                   hand_cropped_out = cv2.resize(hand_cropped_out, (128, 96), cv2.INTER_AREA)
                   hand_cropped_out = hand_cropped_out.reshape((1, 128, 96, 1)).astype('float32')/255
                   prediction = model.predict(hand_cropped_out)
                   pred_indx = np.argmax(prediction)
                   print(pred_indx)
                   if (gesture_device_map[f"{pred_indx}"]["enabled"] == "true"):
                       
                       if not t1.is_alive():
                          t1.start()

                       dev_state = get_status_to_change(pred_indx)
                       req_dict = {"dev_id":f"{pred_indx}", "state":f"{dev_state}"}
                       Qu.put(req_dict)
                       print(req_dict)
                       #  Else everything will be handled by handle_request_from_queue thread if enabled--->it will run forever 
                    
                
                #dev_id_state = get_status_to_change(pred_indx)
                #req_dict = {"dev_id":f"{pred_indx}", "state":f"{dev_id_state}"}
                
            i+=1
            if (i > 40):
                i = 0



##################################################### THREADS #############################################################################            
t2 = threading.Thread(target=handle_gesture)       
################################################## The web server ############################################################################
app = Flask(__name__)
CORS(app)
@app.route('/')
def index():
    return render_template('index.html')
    
# @app.route('/devices', methods=['GET'])
# def show_devices():
#     return render_template('devices.html')

@app.route('/handleDevice', methods=['POST'])
def trigger_devices():
    global Qu
    global t1
    if not t1.is_alive():
        t1.start()
    if request:
        if request.method == "POST":
            content = request.get_json()
            req = {"dev_id":content["dev_id"], "state":content["state"]}
            print(req)
            Qu.put(req)
            return redirect("/")
            
@app.route("/handleWebCam", methods=['POST'])
def handle_web_cam():
    global t2
    global GESTURE_CONTROL_ENABLED
    if request:
        if request.method == "POST":
            command = request.get_json()
            if command["state"] == 'activate':
                GESTURE_CONTROL_ENABLED = True
                if not t2.is_alive():
                    t2.start()
            elif command["state"] == "deactivate":
                GESTURE_CONTROL_ENABLED = False
            
            return redirect('/')

#     #Set flag to Enabled and start thread
#     #To stop it set thread to Disabled state
#     pass


if __name__ == 'main':
    # t1.start()
    app.run(debug=True)

# encoding: utf-8
import sys
import re
import cv2
from graph import *

import face_inference
import Head_pose_inference

import client
import threading
import time

import ChannelManager


lenofUrl = len(sys.argv)
# The number of parameters is incorrect.
if lenofUrl <= 1:
    print("[ERROR] Please input mp4/Rtsp URL")
    sys.exit()
elif lenofUrl >= 3:
    print("[ERROR] param input Error")
    sys.exit()


URL = sys.argv[1]
# match Input parameter format
URL1 = re.match('rtsp://', URL)
URL2 = re.search('.mp4', URL)


# Determine if it is a mp4 video based on matching rules
if URL1 is None:
    if URL2 is None:
        print("[ERROR] should input correct URL")
        sys.exit()
    else:
        mp4_url = True
else:
    mp4_url = False

# 实例化两个推理类
face_app = face_inference.FaceInference()
if face_app.graph is None:
        sys.exit(1)

head_pose = Head_pose_inference.HeadposeInference()
if head_pose.graph is None:
        sys.exit(1)

clientsocket = client.PresenterSocketClient((presenter_ip, presenter_port), 5, None)
if clientsocket is None:
    print('clientsocket is None')
    sys.exit(1)

# Create a thread, bind a thread function.
# the thread function will block after establishing a connection
thread_1 = threading.Thread(target=clientsocket.start_connect)
# Set the thread as a background thread.
# After the main thread ends, the background thread will stop regardless of whether it has finished running
thread_1.setDaemon(True)
# Thread function execution, establish a connection
thread_1.start()
# Provide sufficient connection time for data transfer of the main thread
time.sleep(0.1)

# Instantiate Channel Manager
channel_manager = ChannelManager.ChannelManager()
# Get message data
data = channel_manager.OpenChannel()
# Send message data to presenter server
clientsocket.send_data(data)

cap = cv2.VideoCapture(URL)
ret, frame = cap.read()

# According to the flag,Perform different processing methods
if mp4_url:
    try:
        while ret:
            # Processing the detection results of a frame of pictures
            ret = Head_pose_inference.dowork(frame,clientsocket,channel_manager,face_app,head_pose)
            if ret is None:
                sys.exit(1)
            # Loop through local video files
            ret, frame = cap.read()
    except Exception as e:
        print("ERROR",e)
    finally:
        # Turn off the camera
        cap.release()
else:
    # Create a queue object for caching image data
    rtsp_queue = client.Queue()
    # Create a thread function, the thread reads a frame of image data from the queue
    # does the inference and sends the result of the inference to presenter server
    sub_thread = threading.Thread(target=Head_pose_inference.sub_dowork,args=(rtsp_queue,clientsocket,channel_manager,face_app,head_pose))
    # Set the thread as a background thread. After the main thread ends,
    # the background thread stops regardless of whether it has finished running.
    sub_thread.setDaemon(True)
    # Start thread function
    sub_thread.start()
    try:
        while ret:
            # Put video frames into the queue
            rtsp_queue.put(frame)
            # Loop read video frame
            ret, frame = cap.read()
    except Exception as e:
        print("ERROR",e)
    finally:
        # Turn off the camera
        cap.release()



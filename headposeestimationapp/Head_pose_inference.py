# encoding=utf-8



from  ConstManager import *
import ModelManager
import hiai
from hiai.nn_tensor_lib import DataType
import numpy as np
import cv2
import client
from face_inference import *
from presenter_types import *
import ChannelManager
import time


class HeadposeInference(object):
    def __init__(self):
        self.graph_id = 1001
        self.model_engine_id = 100
        # 一组保存三个角度值->一组保存当前的头部姿势
        self.resultList = []
        # 保存着人脸关键点坐标,一组为136个float型数据
        self.facepointList = []
        # 实例化模型管理类
        self.model = ModelManager.ModelManager()
        self.width = 224
        self.height = 224
        # 描述推理模型以及初始化Graph
        self.graph = None
        self._getgraph()

    def __del__(self):
        self.graph.destroy()

    def _getgraph(self):
        # 描述推理模型
        inferenceModel = hiai.AIModelDescription('head_pose_inference', head_pose_model_path)
        # 初始化Graph
        self.graph = self.model.CreateGraph(inferenceModel,self.graph_id,self.model_engine_id)
        if self.graph is None:
            print "Init Graph failed"

    # 列表中有三个float值,代表三种头部姿势角度，依次为pitch,yaw.roll
    def head_status_get(self):
        for i in range(len(self.resultList)):
            # 初始化标志位
            fg_pitch = True
            fg_yaw = True
            fg_roll = True
            # 初始化字符串
            head_status_string = "头部"
            if self.resultList[i][0] < -20:
                head_status_string = head_status_string + "大幅度抬头"
            elif self.resultList[i][0] < -10:
                head_status_string = head_status_string + "小幅度抬头"
            elif self.resultList[i][0] > 20:
                head_status_string = head_status_string + "大幅度低头"
            elif self.resultList[i][0] > 10:
                head_status_string = head_status_string + "小幅度低头"
            else:
                fg_pitch = False
            if self.resultList[i][1] < -23:
                head_status_string = head_status_string + "大幅度左转"
            elif self.resultList[i][1] < -10:
                head_status_string = head_status_string + "小幅度左转"
            elif self.resultList[i][1] > 23:
                head_status_string = head_status_string + "大幅度右转"
            elif self.resultList[i][1] > 10:
                head_status_string = head_status_string + "小幅度右转"
            else:
                fg_yaw = False
            if self.resultList[i][2] < -20:
                head_status_string = head_status_string + "大幅度右摆"
            elif self.resultList[i][2] < -10:
                head_status_string = head_status_string + "小幅度右摆"
            elif self.resultList[i][2] > 20:
                head_status_string = head_status_string + "大幅度左摆"
            elif self.resultList[i][2] > 10:
                head_status_string = head_status_string + "小幅度左摆"
            else:
                fg_roll = False
            if fg_pitch is False and fg_yaw is False and fg_roll is False:
                head_status_string = head_status_string + "姿势端正"
            self.resultList[i] = head_status_string


    '''
    1.定义输入Tensor的格式
    2.调用推理接口
    3.对一帧推理的正确结果保存到self.resultList中
    '''
    def Inference(self,nparryList,boxList):
        if not (isinstance(nparryList,list) and isinstance(boxList,list)):
            return False
        # 将上一帧图片包含每一个人脸的头部姿势描述清空
        del(self.resultList[:])
        # 将上一帧图片包含每一个人脸的68个关键点清空
        del(self.facepointList[:])

        for i in range(len(nparryList)):
            if isinstance(nparryList[i],np.ndarray) is None:
                print ("please check your input format.")
                return False
            else:
                box_width = boxList[i][2] - boxList[i][0]
                box_height = boxList[i][3] - boxList[i][1]
                resized_image = cv2.resize(nparryList[i],(self.width,self.height))
                inputImageTensor = hiai.NNTensor(resized_image, self.height, self.width, 3, 'testImage', DataType.UINT8_T,
                                                self.height * self.width * 3)
                nntensorList = hiai.NNTensorList(inputImageTensor)
                # 调用推理接口
                resultList = self.model.Inference(self.graph, nntensorList)
                if resultList is not None:
                    # pitch yaw roll
                    # *50
                    # 每次循环完后都要保存结果到self.resultList
                    self.resultList.append(
                        [resultList[1][0][0][0][0] * 50, resultList[1][0][0][0][1] * 50, resultList[1][0][0][0][2] * 50])
                    HeadPosePoint = []
                    for j in range(136):
                        if j % 2 == 0:
                            HeadPosePoint.append((1+resultList[0][0][0][0][j]) / 2 * box_width + boxList[i][0])
                        else:
                            HeadPosePoint.append((1+resultList[0][0][0][0][j]) / 2 * box_height + boxList[i][1])
                    self.facepointList.append(HeadPosePoint)
                else:
                    print ('not inference head pose in this frame.')
                    return False
        # 判断此时的头部姿势
        HeadposeInference.head_status_get(self)
        return True

def dowork(src_img,clientsocket,channel_manager,face_app,head_pose):
    res = face_app.Inference(src_img)
    if res is None:
        return False
    res = head_pose.Inference(face_app.nparray, face_app.boxList)
    if res is None:
        return False
    image_frame = ImageFrame()
    image_frame.format = 0
    image_frame.width = src_img.shape[1]
    image_frame.height = src_img.shape[0]
    image_frame.data = cv2.imencode(".jpg", src_img)[1].tobytes()
    for i in range(len(face_app.boxList)):
        tmp = DetectionResult()
        tmp.lt.x = int(face_app.boxList[i][0])
        tmp.lt.y = int(face_app.boxList[i][1])
        tmp.rb.x = int(face_app.boxList[i][2])
        tmp.rb.y = int(face_app.boxList[i][3])
        tmp.result_text = head_pose.resultList[i]+'--'
        for j in range(68):
            tmp.result_text += str(int(head_pose.facepointList[i][j*2]))+','
            tmp.result_text += str(int(head_pose.facepointList[i][j*2+1]))+' '
        image_frame.detection_results.append(tmp)
    clientsocket.send_data(channel_manager.PackRequestData(image_frame))
    return True


def sub_dowork(rtsp_queue,clientsocket,channel_manager,face_app,head_pose):
    while True:
        # Take a frame of image data from the queue
        frame = rtsp_queue.get()
        if frame is None:
            # If the current queue is empty, wait 100ms
            time.sleep(0.1)
            continue
        # Perform model inference
        dowork(frame,clientsocket,channel_manager,face_app,head_pose)






















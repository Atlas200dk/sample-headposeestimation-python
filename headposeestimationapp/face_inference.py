# encoding=utf-8


from  ConstManager import *
import ModelManager
import hiai
from hiai.nn_tensor_lib import DataType
import numpy as np
import cv2

'''
人脸检测模型不需要对齐，输入300x300,图像输入必须处理成numpy格式
'''
class FaceInference(object):
    def __init__(self):
        # 由用户指定人脸检测推理引擎的所在Graph的id号
        self.graph_id = 1000
        self.model_engine_id = 100
        # 基于输入图片的人脸框坐标
        self.boxList = []
        # 一帧图片上crop出的人脸图片(以numpy数组形式保存)
        self.nparray = []
        # 实例化模型管理类
        self.model = ModelManager.ModelManager()
        self.width = 300
        self.height = 300
        self.M_left = -0.15
        self.M_right = 0.15
        self.M_top = -0.1
        self.M_bottom = 0.25
        # 描述推理模型以及初始化Graph
        self.graph = None
        self._getgraph()

    def __del__(self):
        self.graph.destroy()

    def _getgraph(self):
        # 描述推理模型
        inferenceModel = hiai.AIModelDescription('face_detection', face_detection_model_path)
        # 初始化Graph
        self.graph = self.model.CreateGraph(inferenceModel,self.graph_id,self.model_engine_id)
        if self.graph is None:
            print "Init Graph failed"

    '''
    1.定义输入Tensor的格式
    2.调用推理接口
    3.对一帧推理的正确结果保存到self.resultList中
    4.根据返回值True和False判断是否推理成功
    '''

    def Inference(self,input_image):
        if isinstance(input_image,np.ndarray) is None:
            return False
        h,w,c = input_image.shape
        resized_image = cv2.resize(input_image,(self.width,self.height))
        inputImageTensor = hiai.NNTensor(resized_image)
        nntensorList = hiai.NNTensorList(inputImageTensor)
        # 将上一帧图片推理出的人脸数据清空
        del(self.boxList[:])
        del(self.nparray[:])
        # 调用推理接口
        resultList = self.model.Inference(self.graph, nntensorList)
        # 将推理结果的数据保存到临时列表
        # 再从临时列表中去筛选出有效的人脸坐标,保存到self.resultList中
        # 从原始图片中crop出的人脸(数据类型为numpy数组),保存到一个列表中self.nparray
        if resultList is not None:
            for i in range(200):
                if (resultList[0][i][0][0][2] > 0.8 and resultList[0][i][0][0][2] <= 1.0):
                    if (resultList[0][i][0][0][3] < 0):
                        resultList[0][i][0][0][3] = 0
                    if (resultList[0][i][0][0][4] < 0):
                        resultList[0][i][0][0][4] = 0
                    rect_width = resultList[0][i][0][0][5] - resultList[0][i][0][0][3]
                    rect_height = resultList[0][i][0][0][6] - resultList[0][i][0][0][4]
                    if (resultList[0][i][0][0][3] != 0 and abs(self.M_left * rect_width) <= resultList[0][i][0][0][3]):
                        resultList[0][i][0][0][3] = resultList[0][i][0][0][3] + self.M_left * rect_width
                    if (resultList[0][i][0][0][4] != 0 and abs(self.M_top * rect_height) <= resultList[0][i][0][0][4]):
                        resultList[0][i][0][0][4] = resultList[0][i][0][0][4] + self.M_top * rect_height
                    resultList[0][i][0][0][5] = resultList[0][i][0][0][5] + self.M_right * rect_width
                    resultList[0][i][0][0][6] = resultList[0][i][0][0][6] + self.M_bottom * rect_height
                    # 人脸框的坐标
                    self.boxList.append([resultList[0][i][0][0][3]*w, resultList[0][i][0][0][4]*h,
                                            resultList[0][i][0][0][5]*w, resultList[0][i][0][0][6]*h])
                    self.nparray.append(input_image[int(self.boxList[i][1]):int(self.boxList[i][3]),int(self.boxList[i][0]):int(self.boxList[i][2])])
                else:
                    break
        else:
            print ('not inference face in this frame.')
            return False
        return True














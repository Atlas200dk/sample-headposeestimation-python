# encoding: utf-8
from enum import Enum


class ContentType(Enum):
    kImage = 0
    kVideo = 1
    # Reserved content type, do not use this
    kReserved = 127


class ImageFormat(Enum):
    kJpeg = 0
    kReserved = 127


class OpenChannelParam(object):
    def __init__(self):
        self.host_ip
        self.port
        self.channel_name
        self.content_type


class Point(object):
        def __init__(self):
            self.x = 0
            self.y = 0


class DetectionResult(object):
    def __init__(self):
        # Coordinates of the upper left corner of the target detection frame
        self.lt = Point()
        # Coordinates of the lower right corner of the target detection frame
        self.rb = Point()
        # Inference result：include Object category and corresponding confidence
        self.result_text = None


class ImageFrame(object):
    def __init__(self):
        # One frame picture format must be JPEG
        self.format = ImageFormat.kJpeg
        # Describe the width of the pictures
        self.width = 0
        # Describe the height of the picture
        self.height = 0
        # Do not define the size of a frame image
        self.size = 0
        # Save data for one frame of image
        self.data = b''
        # Detection results for a frame of pictures
        self.detection_results = []

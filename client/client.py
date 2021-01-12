from picamera import PiCamera
from threading import Thread, active_count
from PIL import Image, ImageFilter
import socket
import struct
import io
import time
import argparse

class PiNetworkVideoStream:
    def __init__(self, server_ip, port, resolution=(320, 240), framerate=32):
        self.clientSocket = socket.socket()
        self.clientSocket.connect((server_ip, port))
        self.client2Server = self.clientSocket.makefile('wb')
        self.server2Client = self.clientSocket.makefile('rb')

        self.camera = PiCamera()
        self.camera.resolution = resolution
        self.camera.framerate = framerate
        self.imageStream = io.BytesIO()

        self.thread = Thread(target=self.sendImage, args=())
        self.cameraStream = self.camera.capture_continuous(self.imageStream, format='jpeg', use_video_port=True)
        self.stopImageStream = False

    def start(self):
        self.thread.start()
        self.listenForCommands()

    def sendImage(self):
        for f in self.cameraStream:
            self.client2Server.write(struct.pack('<L', self.imageStream.tell()))
            self.client2Server.flush()
            self.imageStream.seek(0)
            self.client2Server.write(self.imageStream.read())
            self.imageStream.seek(0)
            self.imageStream.truncate()

            if self.stopImageStream:
                self.client2Server.write(struct.pack('<L', 0))
                self.client2Server.flush()
                break

    def listenForCommands(self):
        while True:
            command = struct.unpack('<L', self.server2Client.read(struct.calcsize('<L')))[0]
            if command == 0:
                self.endStreaming()
                return
            elif command == 1:
                self.interuptStreaming()
            elif command == 2:
                self.resumeStreaming()
            else:
                self.processImage(command)
    
    def endStreaming(self):
        print('Request to end stream')
        self.stopImageStream = True
        if active_count() > 1:
            self.thread.join()
        self.client2Server.close()
        self.server2Client.close()
        self.clientSocket.close()
        print('Stream ended')
    
    def interuptStreaming(self):
        print('Request to interupt streaming')
        self.stopImageStream = True
        self.thread.join()
        print('Streaming interupted')
    
    def processImage(self, filter):
        print('Request to process image')
        self.stopImageStream = True
        targetImageLen = struct.unpack('<L', self.server2Client.read(struct.calcsize('<L')))[0]
        targetImageStream = io.BytesIO()
        targetImageStream.write(self.server2Client.read(targetImageLen))
        targetImage = Image.open(targetImageStream)
        
        if filter == 3:
            processedImage = targetImage.filter(ImageFilter.CONTOUR)
        elif filter == 4:
            processedImage = targetImage.filter(ImageFilter.BLUR)
        elif filter == 5:
            processedImage = targetImage.filter(ImageFilter.SHARPEN)
        else:
            print(filter, 'Unknown filter')
            processedImage = targetImage
        
        processedImageStream = io.BytesIO()
        processedImage.save(processedImageStream, 'JPEG')
        self.client2Server.write(struct.pack('<L', processedImageStream.tell()))
        self.client2Server.flush()
        processedImageStream.seek(0)
        self.client2Server.write(processedImageStream.read())
        self.client2Server.flush()
        print('Image processed')

    def resumeStreaming(self):
        print('Request to resume streaming')
        self.stopImageStream = False
        self.thread = Thread(target=self.sendImage, args=())
        self.thread.start()
        print('Streaming resumed')


ap = argparse.ArgumentParser()
ap.add_argument('-si', '--server-ip', type=str, help='the lan ip of desktop')
ap.add_argument('-p', '--port', type=int, default=8000, help='port number where server listens for connections')
ap.add_argument('-res', '--resolution', type=str, help='widthxheight', default='320x240')
args = vars(ap.parse_args())

[width, height] = args['resolution'].split('x')
vs = PiNetworkVideoStream(args['server_ip'], int(args['port']), (int(width), int(height)))
vs.start()

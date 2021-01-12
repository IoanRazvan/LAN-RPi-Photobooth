from __future__ import print_function
from PIL import Image, ImageTk
import tkinter as tki
import socket
import threading
import struct
import io
from functools import partial
import argparse

class PhotoBoothApp:
    def __init__(self, ip, port):
        self.server_socket = socket.socket()
        self.server_socket.bind((ip, port))
        self.server_socket.listen(0)
        connection = self.server_socket.accept()[0]
        self.client2Server = connection.makefile('rb')
        self.server2Client = connection.makefile('wb')

        self.root = tki.Tk()
        self.buttonsFrame = tki.Frame(self.root)
        self.imagesFrame = tki.Frame(self.root)
        self.imagesFrame.pack(side='top')
        self.panel1 = None
        self.panel2 = None

        self.snapshotBtn = tki.Button(self.root, text='Snapshot', command=self.takeSnapshot)
        self.snapshotBtn.pack(side='bottom', fill='both', expand='yes', padx=10, pady=10)

        self.backBtn = tki.Button(self.buttonsFrame, text='Back', command=self.goBack)
        self.backBtn.pack(side='left', pady=10, padx=5, fill='x')

        self.contourBtn = tki.Button(self.buttonsFrame, text='Contour', command=partial(self.applyEffect, effect=3))
        self.contourBtn.pack(side='left', pady=10, padx=5, fill='x')

        self.blurBtn = tki.Button(self.buttonsFrame, text='Blur', command=partial(self.applyEffect, effect=4))
        self.blurBtn.pack(side='left', pady=10, padx=5, fill='x')

        self.sharpBtn = tki.Button(self.buttonsFrame, text='Sharp', command=partial(self.applyEffect, effect=5))
        self.sharpBtn.pack(side='left', pady=10, padx=5, fill='x')

        self.endApp = False
        self.thread = threading.Thread(target=self.videoLoop, args=())

        self.root.wm_title('Stream')
        self.root.wm_protocol('WM_DELETE_WINDOW', self.onClose)
        
    def start(self):
        self.thread.start()
        self.root.mainloop()

    def takeSnapshot(self):
        self.server2Client.write(struct.pack('<L', 1))
        self.server2Client.flush()
        self.snapshotBtn.pack_forget()
        self.buttonsFrame.pack(side='bottom', fill='both')
    
    def videoLoop(self):
        while True:
            imageLen = struct.unpack('<L', self.client2Server.read(struct.calcsize('<L')))[0]

            if not imageLen:
                break
            
            imageStream = io.BytesIO()
            imageStream.write(self.client2Server.read(imageLen))
            imageStream.seek(0)
            self.lastImage = Image.open(imageStream)
            panel1Image = ImageTk.PhotoImage(self.lastImage)
            
            if self.panel1 is None:
                self.panel1 = tki.Label(self.imagesFrame, image=panel1Image)
                self.panel1.image = panel1Image
                self.panel1.pack(side='left', padx=10, pady=10)
            else:
                self.panel1.configure(image=panel1Image)
                self.panel1.image = panel1Image

        if self.endApp:
            self.cleanup()

    def onClose(self):
        self.endApp = True
        self.server2Client.write(struct.pack('<L', 0))
        self.server2Client.flush()
        if threading.active_count() == 1:
            self.cleanup()
        
    def cleanup(self):
        self.server2Client.close()
        self.client2Server.close()
        self.server_socket.close()
        self.root.quit()
    
    def goBack(self):
        self.server2Client.write(struct.pack('<L', 2))
        self.server2Client.flush()
        self.buttonsFrame.pack_forget()
        if self.panel2:
            self.panel2.pack_forget()
        self.snapshotBtn.pack(side='bottom', fill='both', expand='yes', padx=10, pady=10)
        self.thread = threading.Thread(target=self.videoLoop, args=())
        self.thread.start()
    
    def applyEffect(self, effect): 
        self.server2Client.write(struct.pack('<L', effect))
        imageStream = io.BytesIO()
        self.lastImage.save(imageStream, 'JPEG')
        self.server2Client.write(struct.pack('<L', imageStream.tell()))
        self.server2Client.flush()
        imageStream.seek(0)
        self.server2Client.write(imageStream.read())
        self.server2Client.flush()
  
        processedImageLen = struct.unpack('<L', self.client2Server.read(struct.calcsize('<L')))[0]
        processedImageStream = io.BytesIO()
        processedImageStream.write(self.client2Server.read(processedImageLen))
        processedImage = Image.open(processedImageStream)
        processedImage = ImageTk.PhotoImage(processedImage)
        
        if self.panel2 is None:
            self.panel2 = tki.Label(self.imagesFrame, image=processedImage)
            self.panel2.image = processedImage
        else:
            self.panel2.configure(image=processedImage)
            self.panel2.image = processedImage
        self.panel2.pack(side='left')

ap = argparse.ArgumentParser()
ap.add_argument('-p', '--port', type=int, default=8000, help='port number to listen on')
args = vars(ap.parse_args())
pb = PhotoBoothApp('0.0.0.0', int(args["port"]))
pb.start()
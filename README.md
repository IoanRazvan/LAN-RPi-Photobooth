# RPi LAN Image Processing Stream

This project was made for the Computer Systems Architecture course. The goal was to demonstrate the ability to capture and process images using a Raspberry Pi. For this purpose, the Raspberry Pi camera module was used because it has it's own Python package.

The project consists of two scripts communicating through the LAN using sockets. The script `client.py` will run on the Raspberry, sending images to the server in the format `image_length` followed by the bytes of an image. The client also opens a new thread to listen for commands coming from the server. The server receives the images and displays them in the graphical interface. Clicking the buttons causes the server to send various requests of action to the client.

## Prerequisites

You will need:

- Raspberry Pi with CSI port and Internet connection
- Raspberry Pi camera module
- Git on both your Raspberry and PC
- Python on both your Raspberry and PC

## How to run

Your Pi needs to be connected to the same LAN as your PC, and you will also need ssh access to it. Clone this repository on your PC and Raspberry using:

```bash
git clone https://github.com/IoanRazvan/LAN-RPi-Photobooth
```

To start the server run the following commands:

```bash
cd LAN-RPi-Photobooth
pip install server/requirements.txt
python server/server.py -p [port to listen on]
```

Which will install the packages needed by the server and run it specifying the port to listen for connections. For the client, you should execute the following commands:

```bash
cd LAN-RPi-Photobooth
pip install client/requirements.txt
python client/client.py -si [ip of the server] -p [port to listen on] -res [resolution of images]
```

Which will install the required packages and start the client specifying the IP of the server, the port on which the communication will take place, and the resolution of the images. After running the above commands, a GUI should start displaying images on your PC.

## Acknowledgements

- [Displaying a video feed with Tkinter](https://www.pyimagesearch.com/2016/05/30/displaying-a-video-feed-with-opencv-and-tkinter/)
- [Capturing to a network stream](https://picamera.readthedocs.io/en/release-1.13/recipes1.html#streaming-capture)

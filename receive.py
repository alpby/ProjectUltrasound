import sys
import Queue
import threading
import time
import pyaudio
import numpy as np
from struct import *
import settings

# create queue elements
frames = Queue.Queue(settings.INLENGTH)
points = Queue.Queue(settings.INLENGTH)
bits = Queue.Queue(settings.INLENGTH / settings.FRAMELENGTH)

# find the frequency of recevied signal
def threadFrames():
    while True:
        if frames.empty():
            time.sleep(0.1)
        else:
            frame = frames.get_nowait()
            fftSample = np.abs(np.fft.fft(frame))
            points.put(fftSample[settings.PEAKINDEX])

tf = threading.Thread(target=threadFrames)
tf.daemon = True
tf.start()

# process the received signal if its frequency is above certain threshold
def threadPoints():
    while True:
        currentPoints = list()
        while len(currentPoints) < settings.FRAMELENGTH:
            if points.empty():
                time.sleep(0.1)
            else:
                currentPoints.append(points.get_nowait())
        while True:
            nextPoint = None
            while nextPoint == None:
                if points.empty():
                    time.sleep(0.1)
                else:
                    nextPoint = points.get_nowait()
            if nextPoint > settings.BOTTOMTHRESHOLD:
                for elem in settings.SEP:
                    bits.put(elem)
                currentPoints = [currentPoints[-1]]
                break
        print("")

        lastBit = list()
        while True:
            if len(currentPoints) == settings.FRAMELENGTH:
                bit = int(int(round(sum(currentPoints) / float(settings.FRAMELENGTH))) > settings.BOTTOMTHRESHOLD)
                currentPoints = list()
                bits.put(bit)
                lastBit.append(bit)

            if len(lastBit) > 3:
                if sum(lastBit) == 0:
                    break
                lastBit = lastBit[1:]
            if points.empty():
                time.sleep(0.1)
            else:
                currentPoints.append(points.get_nowait())

tp = threading.Thread(target=threadPoints)
tp.daemon = True
tp.start()

# decode received signal and write it down
def threadBits():
    while True:
        currentBits = list()
        # while the last two characters are not the settings.SEP
        while len(currentBits) < 2 or currentBits[-len(settings.SEP):] != settings.SEP:
            if bits.empty():
                time.sleep(0.1)
            else:
                currentBits.append(bits.get_nowait())
        try:
            decoded = settings.DECODEPSK[''.join([str(i) for i in currentBits[:-len(settings.SEP)]])]
        except:
            decoded = ''
        sys.stdout.write(decoded)
        sys.stdout.flush()

tb = threading.Thread(target=threadBits)
tb.daemon = True
tb.start()

# yield n-sized chunks from l
def chunks(l, n):
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

# define callback function to use whenever new audio data is needed
def callback(inputData, frame_count, time_info, status):
    # unpacking frames accoring to given format
    unpacked = [unpack('h', frame)[0] for frame in list(chunks(inputData, 2))]

    # put frames into the queue
    for frame in list(chunks(unpacked, settings.CHUNK)):
        if not frames.full():
            frames.put_nowait(frame)
    return (inputData, pyaudio.paContinue)

# instantiate PyAudio
p = pyaudio.PyAudio()

# open stream using callback
stream = p.open(format = settings.FORMAT, channels = settings.CHANNELS, rate = settings.RATE,input = True, frames_per_buffer = settings.FRAMESPERBUFFER, stream_callback=callback)

print ("\nListening Frequency is %sHz! To quit use Ctrl-C!\n" % settings.FREQUENCY)

# start the stream
stream.start_stream()

# wait for stream to finish
try:
    while stream.is_active():
        time.sleep(0.1)
# stop the stream using CTRL-C
except KeyboardInterrupt:
    print ("\nYou hit CTRL-C")

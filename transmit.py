import pyaudio
import settings
import numpy as np
from struct import *

# instantiate PyAudio
p = pyaudio.PyAudio()

# open stream using callback
stream = p.open(format = settings.FORMAT, channels = settings.CHANNELS, rate = settings.RATE, output = True)

print "\nTalk in ultrasound! To quit use quit() or exit()\n"

while True:
    # write a message to be sent using ultrasound frequencies
    message = raw_input("> ")
    if message == "exit()" or message == "quit()":
        break

    # encode the transmitted message
    encoded = ""
    for m in message:
        encoded += settings.PSK[m] + "00"

    # modulate the encoded signal
    outputBuffer = list()
    transmitted = ""
    for i, bit in enumerate(encoded):
        sendTone = [0] * settings.DATASIZE
        if bit == '1':
            for j in range(settings.DATASIZE):
                sendTone[j] = int(settings.AMPLITUDE * np.cos(float(settings.FREQUENCY) * 2 * np.pi/settings.RATE * j))

        # envelope transmitted message
        sendTone[:len(sendTone)] *= np.linspace(0, 1, len(sendTone)) * np.linspace(1, 0, len(sendTone))

        # packing frames accoring to given format
        for frame in sendTone:
            transmitted += pack('h', frame)

    # play stream
    stream.write(transmitted)

# stop stream
stream.stop_stream()
stream.close()

# close PyAudio
p.terminate()

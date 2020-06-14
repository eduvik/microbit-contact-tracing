from microbit import *
import radio
import time
import os
import machine

# all times in milliseconds
DELAY_BETWEEN_BROADCASTS = 10000
CLOSE_CONTACT_TIME = 300000
TIMEOUT = 30000  # max time that we can not have a ping from a device while still considering it to be in close contact
TIME_BETWEEN_DATA_SAVES = 300000  # save data file this often

RSSI_THRESHOLD = -70

INFECTED_FILENAME = "infected"

ID = machine.unique_id()[4:8]
full_id = machine.unique_id()
test_ids = (full_id[0:4],
            full_id[1:5],
            full_id[2:6],
            full_id[3:7],
            full_id[4:8],
            full_id[5:8] + full_id[0:1],
            full_id[6:8] + full_id[0:2],
            full_id[7:8] + full_id[0:3],
            )

def hex2str(b):
    return "".join([hex(a)[2:] for a in b])


DATA_FILENAME = hex2str(ID) + "-1.csv"
# check if data file exists; create new name to prevent overwriting
i = 2
while True:
    try:
        f = open(DATA_FILENAME)
        f.close()
        DATA_FILENAME = hex2str(ID) + "-" + str(i) + ".csv"
        i += 1
    except:
        break  # file doesn't exist, so filename is safe to use

contacts = {}
close_contacts = {}
last_data_save = 0

# check if this device is infected
try:
    f = open(INFECTED_FILENAME)
    infected = 1
    f.close()
except OSError:
    infected = 0

radio.on()

while True:
    #if both buttons are pressed, dump data to serial port.
    if button_a.is_pressed() and button_b.is_pressed():
        display.show((Image.ARROW_N, Image("00000:"*5)), delay=100, wait=False, loop=True)
        for i in range(50):
            print()
        for filename in os.listdir():
            if filename[-4:] == ".csv":
                f = open(filename, "rb")
                print("-----START:" + filename)
                print("Receiver,Sender,First Contact Time (min),Last Contact Time (min)")  #write header here to save disk space
                while True:
                    sleep(50)  # prevent serial overruns
                    l = f.readline()
                    if not l:
                        break
                    print("x" + hex2str(ID) +  # adding x to every ID number so spreadsheets don't try to interpret as number/scientific notation
                          ",x" + hex2str(l[0:4]) +
                          "," + str(int.from_bytes(l[4:6], "big")) +
                          "," + str(int.from_bytes(l[6:8], "big")) +
                          (",!" if (len(l) >= 9 and l[8] == "!") else ""))
        display.clear()

    #check for received messages and process
    d = radio.receive_full()
    while d:
        received_infected = False
        received_id, rssi, timestamp = d
        timestamp = int(timestamp/1000)  # timestamp from radio is in microseconds; convert to milliseconds
        if len(received_id) == 5 and received_id[4] == '!':  # infected contacts are marked with a ! after the ID
            received_infected = True
            received_id = received_id[:-1]  # trim infected marker
        if rssi > RSSI_THRESHOLD:
            if received_id in contacts:
                if contacts[received_id][1] + TIMEOUT < timestamp:  # previous contact timed out; start again
                    contacts[received_id] = (timestamp, timestamp)  # (first contact, last timestamp)
                else:
                    contacts[received_id] = (contacts[received_id][0], timestamp)  # update last timestamp
            else:
                contacts[received_id] = (timestamp, timestamp)  # (first contact, last timestamp)

            if contacts[received_id][1] - contacts[received_id][0] > CLOSE_CONTACT_TIME:
                # record close contact
                contactID = received_id + (contacts[received_id][0]//60000).to_bytes(2, 'big')  # "4 bytes serial, then 2 bytes for first timestamp"
                close_contacts[contactID] = (contacts[received_id][1]//60000).to_bytes(2, 'big') + (b"!" if received_infected else b"")  # (last timestamp, infected)
                if not infected and received_infected:
                    infected = 1
                    open(INFECTED_FILENAME, "w").close()
        d = radio.receive_full()  # get next message from queue

    #send message
    for tid in test_ids:
        radio.send_bytes(tid + "!" if infected else tid)  # append ! to ID if we're infected
    sleep(DELAY_BETWEEN_BROADCASTS)

    #save data to file
    if close_contacts and last_data_save + TIME_BETWEEN_DATA_SAVES < time.ticks_ms():
        f = open(DATA_FILENAME, "wb")
        for contactID, contact in close_contacts.items():
            f.write(contactID + contact + "\n")
            # line format: IIIIFFLL!\n
            # IIII = ID of other device
            # FF = initial contact timestampe
            # LL = last contact timestamp
            # ! = optional infected indicator
            # \n end of record
        f.close()

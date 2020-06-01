from microbit import *
import radio
import time
import os

def get_serial_number(type=hex):
    NRF_FICR_BASE = 0x10000000
    DEVICEID_INDEX = 25 # deviceid[1]
    @micropython.asm_thumb
    def reg_read(r0):
        ldr(r0, [r0, 0])
    n = reg_read(NRF_FICR_BASE + (DEVICEID_INDEX*4))
    return type(n if n > 0 else n & (2**32-1))

radio.on()

ID = get_serial_number()[2:]

# all times in milliseconds
DELAY_BETWEEN_BROADCASTS = 10 * 1000
CLOSE_CONTACT_TIME = 5 * 60 * 1000
TIMEOUT = 30 * 1000  # max time that we can not have a ping from a device while still considering it to be in close contact
TIME_BETWEEN_DATA_SAVES = 5 * 60 * 1000  # save data file this often

RSSI_THRESHOLD = -60

INFECTED_FILENAME = "infected"

DATA_FILENAME = ID + "-1.csv"
# check if data file exists; create new name to prevent overwriting
i = 2
while True:
    try:
        f = open(DATA_FILENAME)
        f.close()
        DATA_FILENAME = ID + "-" + str(i) + ".csv"
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

while True:
    #if both buttons are pressed, dump data to serial port.
    if button_a.is_pressed() and button_b.is_pressed():
        for i in range(50):
            print()
        for filename in os.listdir():
            if filename[-4:] == ".csv":
                f = open(filename)
                print("-----START:" + filename)
                print("Receiver,Sender,First Contact (min),Total Contact Time (min)")  #write header here to save disk space
                while True:
                    l = f.readline()
                    if not l:
                        break
                    print(ID + "," + l, end='')

    #check for received messages and process
    d = radio.receive_full()
    while d:
        received_infected = False
        display.show([Image.SQUARE, Image.SQUARE_SMALL], delay=50, wait=True, clear=True)
        msg, rssi, timestamp = d
        timestamp = int(timestamp/1000)  # timestamp from radio is in microseconds; convert to milliseconds
        received_id = str(msg[3:], 'utf8')  #strip first three chars off the front; these are not part of the message
        if received_id[-1] == '!':  #infected contacts are marked with a ! after the ID
            received_infected = True
            received_id = received_id[:-1] # trim infected marker
        if rssi > RSSI_THRESHOLD:
            if received_id in contacts:
                if contacts[received_id][1] + TIMEOUT < timestamp:  # previous contact timed out; start again
                    contacts[received_id] = (timestamp, timestamp) # (first contact, last timestamp)
                else:
                    contacts[received_id] = (contacts[received_id][0], timestamp)  # update last timestamp
            else:
                contacts[received_id] = (timestamp, timestamp) # (first contact, last timestamp)

            if contacts[received_id][1] - contacts[received_id][0] > CLOSE_CONTACT_TIME:
                # record close contact
                contactID = received_id + ":" + str(contacts[received_id][0]//60000) # "SERIAL:first_timestamp"
                close_contacts[contactID] = (contacts[received_id][1]//60000, received_infected) # (last timestamp, infected)
                if not infected and received_infected:
                    infected = 1
                    open(INFECTED_FILENAME, "w").close()
        d = radio.receive_full()  # get next message from queue

    #send message
    sleep(DELAY_BETWEEN_BROADCASTS/2)
    radio.send(ID + "!" if infected else ID)  # append ! to ID if we're infected
    display.show([Image.SQUARE_SMALL, Image.SQUARE], delay=50, wait=True, clear=True)
    sleep(DELAY_BETWEEN_BROADCASTS/2)

    #save data to file
    if close_contacts and last_data_save + TIME_BETWEEN_DATA_SAVES < time.ticks_ms():
        f=open(DATA_FILENAME, "w")
        for contactID, contact in close_contacts.items():
            user_id, first_timestamp = contactID.split(":")
            contact_time = contact[0] - int(first_timestamp)
            line = user_id + "," + first_timestamp + "," + str(contact_time)
            if contact[1]:  # infected
                line += ",1"
            f.write(line + "\n")
        f.close()

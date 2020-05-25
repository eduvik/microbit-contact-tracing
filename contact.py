from microbit import *
import radio
import time

def get_serial_number(type=hex):
    NRF_FICR_BASE = 0x10000000
    DEVICEID_INDEX = 25 # deviceid[1]

    @micropython.asm_thumb
    def reg_read(r0):
        ldr(r0, [r0, 0])
    return type(reg_read(NRF_FICR_BASE + (DEVICEID_INDEX*4)))

radio.on()

ID = get_serial_number()

# all times in milliseconds
DELAY_BETWEEN_BROADCASTS = 10*1000
CLOSE_CONTACT_TIME = 1*60*1000
TIMEOUT = 30 * 1000  # max time that we can not have a ping from a device while still considering it to be in close contact
TIME_BETWEEN_DATA_SAVES = 1 * 60 * 1000  # save data file this often

RSSI_THRESHOLD = -60
DATA_FILENAME = "data.csv"

contacts = {}
close_contacts = {}
last_data_save = 0

while True:
    #if both buttons are pressed, dump data to serial port.
    if button_a.is_pressed() and button_b.is_pressed():
        for i in range(50):
            print()
        f=open(DATA_FILENAME)
        while True:
            l = f.readline()
            if not l:
                break
            print(l, end='')

    d = radio.receive_full()
    while d:  #process messages in buffer
        display.show([Image.SQUARE, Image.SQUARE_SMALL], delay=50, wait=True, clear=True)
        msg, rssi, timestamp = d
        timestamp = int(timestamp/1000)  # timestamp from radio is in microseconds; convert to milliseconds
        received_id = str(msg[3:], 'utf8')  #strip first three chars off the front; these are not part of the message

        if rssi > RSSI_THRESHOLD:
            if received_id in contacts:
                if contacts[received_id]['last_timestamp'] + TIMEOUT < timestamp:  # previous contact timed out; start again
                    contacts[received_id] = {'first_contact': timestamp, 'last_timestamp': timestamp}
                    #print("A", received_id, contacts[received_id])
                else:
                    contacts[received_id]['last_timestamp'] = timestamp  # update last timestamp
                    #print("B", received_id, contacts[received_id])
            else:
                contacts[received_id] = {'first_contact': timestamp, 'last_timestamp': timestamp}
                #print("C", received_id, contacts[received_id])

            if contacts[received_id]['last_timestamp'] - contacts[received_id]['first_contact'] > CLOSE_CONTACT_TIME:
                # record close contact
                contactID = received_id + ":" + str(contacts[received_id]['first_contact'])
                close_contacts[contactID] = contacts[received_id]['last_timestamp']
                #print("CLOSE", contactID, close_contacts[contactID])
        d = radio.receive_full()  # get next message from queue
    sleep(DELAY_BETWEEN_BROADCASTS/2)
    radio.send(ID)
    display.show([Image.SQUARE_SMALL, Image.SQUARE], delay=50, wait=True, clear=True)
    sleep(DELAY_BETWEEN_BROADCASTS/2)

    if close_contacts and last_data_save + TIME_BETWEEN_DATA_SAVES < time.ticks_ms():
        f=open(DATA_FILENAME, "w")
        f.write("ID,Time of First Contact (ms),Total Contact Time (ms)\n")
        for contactID, last_timestamp in close_contacts.items():
            user_id, first_timestamp = contactID.split(":")
            contact_time = last_timestamp - int(first_timestamp)
            f.write(user_id + "," + first_timestamp + "," + str(contact_time) + "\n")
        f.close()

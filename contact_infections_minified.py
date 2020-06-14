from microbit import*
import radio
import time
import os
import machine
DELAY_BETWEEN_BROADCASTS=10000
CLOSE_CONTACT_TIME=300000
TIMEOUT=30000 
TIME_BETWEEN_DATA_SAVES=300000 
RSSI_THRESHOLD=-70
INFECTED_FILENAME="infected"
ID=machine.unique_id()[4:]
def hex2str(b):
 return "".join([hex(a)[2:]for a in b])
DATA_FILENAME=hex2str(ID)+"-1.csv"
i=2
while True:
 try:
  f=open(DATA_FILENAME)
  f.close()
  DATA_FILENAME=hex2str(ID)+"-"+str(i)+".csv"
  i+=1
 except:
  break 
contacts={}
close_contacts={}
last_data_save=0
try:
 f=open(INFECTED_FILENAME)
 infected=1
 f.close()
except OSError:
 infected=0
radio.on()
while True:
 if button_a.is_pressed()and button_b.is_pressed():
  display.show((Image.ARROW_N,Image("00000:"*5)),delay=100,wait=False,loop=True)
  for i in range(50):
   print()
  for filename in os.listdir():
   if filename[-4:]==".csv":
    f=open(filename,"rb")
    print("-----START:"+filename)
    print("Receiver,Sender,First Contact Time (min),Last Contact Time (min)") 
    while True:
     sleep(50) 
     l=f.readline()
     if not l:
      break
     print("x"+hex2str(ID)+",x"+hex2str(l[0:4])+","+str(int.from_bytes(l[4:6],"big"))+","+str(int.from_bytes(l[6:8],"big"))+(",!" if(len(l)>=9 and l[8]=="!")else ""))
  display.clear()
 d=radio.receive_full()
 while d:
  received_infected=False
  received_id,rssi,timestamp=d
  timestamp=int(timestamp/1000) 
  if len(received_id)==5 and received_id[4]=='!': 
   received_infected=True
   received_id=received_id[:-1] 
  if rssi>RSSI_THRESHOLD:
   if received_id in contacts:
    if contacts[received_id][1]+TIMEOUT<timestamp: 
     contacts[received_id]=(timestamp,timestamp) 
    else:
     contacts[received_id]=(contacts[received_id][0],timestamp) 
   else:
    contacts[received_id]=(timestamp,timestamp) 
   if contacts[received_id][1]-contacts[received_id][0]>CLOSE_CONTACT_TIME:
    contactID=received_id+(contacts[received_id][0]//60000).to_bytes(2,'big') 
    close_contacts[contactID]=(contacts[received_id][1]//60000).to_bytes(2,'big')+(b"!" if received_infected else b"") 
    if not infected and received_infected:
     infected=1
     open(INFECTED_FILENAME,"w").close()
  d=radio.receive_full() 
 radio.send_bytes(ID+"!" if infected else ID) 
 sleep(DELAY_BETWEEN_BROADCASTS)
 if close_contacts and last_data_save+TIME_BETWEEN_DATA_SAVES<time.ticks_ms():
  f=open(DATA_FILENAME,"wb")
  for contactID,contact in close_contacts.items():
   f.write(contactID+contact+"\n")
  f.close()
# Created by pyminifier (https://github.com/liftoff/pyminifier)

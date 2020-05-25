# microbit-contact-tracing
A contact tracing system using micro:bits

Flash either contact.py or contact_infections.py onto a microbit (need to be converted to hex first - use https://python.microbit.org)

Each micro:bit will periodically send a message containing its ID (serial number). It will also receive such messages from any micro:bit nearby. If the signal strength is strong, it notes a contact. If a contact has been close for a certain amount of time, it gets logged in a file. The file can be dumped to the serial port by pressing and holding both A & B buttons.

The contact_infections.py variant has an 'infected' flag. If your micro:bit is in prolonged contact with an infected micro:bit, it too will get infected. This is logged in an extra field in the data file, as well as the presence of an empty file 'infected' on the microbit itself.

Coming soon - easy tool to download data via web browser; probabilistic infections.

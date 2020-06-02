import lzma, base64, json, sys

# Creates an 'import' link on python.microbit.org for a given python file (specified on the command line)
# This is done by putting together a dictionary in a particular format, dumping it as JSON, compressing it,
# then Base64 encoding, finally appending to the URL to make a 'shareable' micro:bit python file

NAME = "Micro:bit project"
COMMENT = ""
if not sys.argv[1]:
    print("no filename supplied")
    exit()
FILENAME = sys.argv[1]

filedata = open(FILENAME).read()
data = {
  "meta": {
        "comment": COMMENT,
        "editor": "python",
        "name": NAME,
      },
 "source": filedata
}
data_json = json.dumps(data).encode('utf8')
data_compressed =  lzma.compress(data_json, format=lzma.FORMAT_ALONE)
data_encoded = base64.b64encode(data_compressed)
url = 'https://python.microbit.org/v/2.0#project:' + data_encoded.decode()
print(url)

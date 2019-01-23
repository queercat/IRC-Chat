# Chat.py - logs live IRC chat for OBS playback.

# Imports
import json # For JSON encoding.
import socket # For regular socket magic.
import ssl # For SSL socket magic.
import codecs # For encoding and unencoding data.
import os # For moving and deleting files.
import datetime # For file names.

# config.json layout
# bot_nick - string, the nick for the bot.
# address - string, the host address for the IRC server to connect to.
# port - unsigned int, the port to connect to
# SSL - bool, ? SSL enabled.
# channel - string, the channel to connect to.

# Location of the config file. Change it if it's somewhere else.
config_location = "./config.json"

def main():
    # Create config and client objects.
    config = parseJSON(config_location)
    client = IRC_Client(config)

    # Cleanups a few old files.
    clean_up(client.output_file)

    # Connect and head into loop.
    sock = client.connect()
    
    # Send the hello message to the IRC server.
    client.handshake(sock)
    client.loop(sock)

    # Close the connection.
    client.close(sock)

# IRC_Client ... an rarted IRC client.
class IRC_Client:
    def __init__(self, config): 
        self.nick = get(config, 'bot_nick')
        self.alt_nick = get(config, 'bot_alt_nick')
        self.real_name = get(config, 'bot_real_name')
        self.user_mode = get(config, 'user_mode')
        self.host_address = get(config, 'host_address')
        self.port = get(config, 'port')
        self.SSL = get(config, 'ssl')
        self.channel = get(config, 'channel')
        self.output_file = get(config, 'output_file')

    # Returns the name of a user in a message.
    def get_name(self, msg):
        start = msg.find(':')
        end = msg.find('!')

        return msg[start + 1:end]

    def get_msg(self, msg):
        first = msg.find(':')
        start = msg.find(':', first + 1)
        end = msg.find('\r')

        if 'ACTION' in msg:
            start = msg.find('ACTION') + len('ACTION')
            end = msg.find('\r', start + 1) - 1

        return msg[start + 1:end]        

    # Recieve data and return it.
    def recv(self, sock):
        data = ""

        while True:
            buffer = parse(str(sock.recv(4096))) # This turns the escaped characters into non-escaped characters.
            data += buffer

            if '\r' in buffer:
                break

            if buffer is '':
                break

        if 'PING' in data:
            self.send(sock, 'PONG')

        if 'PRIVMSG' in data:
            name = self.get_name(data)
            msg = self.get_msg(data)
            seperator = ': '

            # Good enough for government work.
            if data.find('ACTION') == data.find(':', data.find(':') + 1) + 2:
                seperator = ' '
                name = '* ' + name

            full_msg = (name + seperator + msg)
            
            log(full_msg, self.output_file)

        if 'JOIN' in data:
            name = self.get_name(data)
            msg = self.get_msg(data)

            full_msg = (name + ' joined ' + msg)
            log(full_msg, self.output_file)
            
        return data

    # Send a msg to the server.
    def send(self, sock, msg):
        sock.send((msg + '\r\n').encode())
        print(self.nick + ': ' + msg)

    # Close the socket. BTW did you know sockets are file descriptors?
    def close(self, sock):
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()

        print('I pulled out I promise.')

        input()

    # Connect using an SSL condom.
    def connect(self):
        hostname = self.host_address
        port = self.port
        context = ssl.create_default_context()
        sock = socket.socket()

        if self.SSL:
            sock = context.wrap_socket(sock, server_hostname=hostname)

        print('Wrap it before you tap it.')

        sock.connect((hostname, port))
        return sock
    
    # It's sort of like an IRC handshake.
    def handshake(self, sock):
        # RFC 2812 3.1
        # 1. (Optional) Pass message -> 2. Nick message or 2. Service message -> 3. User message
        # PASS [password]
        # NICK [nick]
        # USER [username] [0 for visible, 8 for invisible] [not used so *] [real name]

        self.sock = sock
        self.recv(sock)

        # # Checks if pass is empty. Strings are truthy and falsy.
        # if self.password: 
        #     pass_msg = 'PASS ' + self.password 
        #     self.send(sock, pass_msg) 

        nick_msg = 'NICK ' + self.nick
        self.send(sock, nick_msg)

        user_msg = 'USER ' + self.nick + ' ' + str(self.user_mode) + ' * ' + self.real_name
        self.send(sock, user_msg)

        self.recv(sock)

        self.send(sock, 'JOIN ' + self.channel)

    # Main loop for IRC stuff.
    def loop(self, sock):
        # Loop structure: RECV -> PARSE (->) ACTION [LOOP]
        while True:
            self.recv(sock)

# parseJSON ... parses the JSON config and returns a JSON obj with config stuff.
def parseJSON(file_location):
    # Open file for reading and then close the file.
    with open(config_location, 'r') as config_file:
        config_data = config_file.read()
    config_file.close()

    config_object = json.loads(config_data)

    return config_object

# Logs messages and other data into a text file.
def log(data, file_location):
    log = open(file_location, 'a+', encoding='utf-8')
    log.write(data + '\r\n\r')
    log.close()

# Cleans up so that files don't conflict.
def clean_up(file_location):
    now = datetime.datetime.now()

    if not os.path.isdir(os.path.dirname(file_location)):
        os.makedirs(os.path.dirname(file_location))

    if os.path.isfile(file_location):
        current_time = str(str(now.year) + '-' + str(now.month) + '-' + str(now.day) + '-' + str(now.hour) + '-' + str(now.minute) + '-' + str(now.second))
        os.rename(file_location, os.path.dirname(file_location) + '/' + current_time + '.txt')

# Simple helper function for getting an element out of an object.
def get(JSON_object, element):
    return JSON_object[element]

# Replaces escaped characters with regular characters.
def parse(string):
    return codecs.getdecoder('unicode_escape')(string)[0]

if __name__ == "__main__":
    main()
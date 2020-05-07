import math
import serial
import threading
import time
import datetime

class AVR(object):
    PortOpen = False
    
    def __init__(self, Device='/dev/ttyAMA0'):
        print ("AVR module init")
        self._WhenLockGained = None
        self._WhenLockLost = None
        self._WhenNewPosition = None
        self._WhenNewSentence = None
        self.IsOpen = False
        self.GPSPosition = {'time': '00:00:00', 'lat': 0.0, 'lon': 0.0, 'alt': 0, 'sats': 0, 'fixtype': 0}
        
        # Serial port /dev/ttyAMA0
        self.ser = serial.Serial()
        self.ser.baudrate = 38400
        self.ser.stopbits = 1
        self.ser.bytesize = 8
        self.ser.timeout = 0
        self.ser.port = Device
        
        self.Commands = []
    

    def ProcessCommand(self, Command, Parameters):       
        if Command == 'GPS':

            # GPS=12:6:41,51.95056,-2.54472,102,6
            Fields = Parameters.split(',')
            
            # print(Fields)
            
            # ['12:6:41', '51.95056', '-2.54472', '102', '6']

            if Fields[1] != '':
                # self.GPSPosition['time'] = Fields[0];
                self.GPSPosition['time'] = datetime.datetime.strptime(Fields[0] + ' ' + Fields[1], '%d/%m/%Y %H:%M:%S')

                if Fields[1] != '':
                    self.GPSPosition['lat'] = float(Fields[2])
                    self.GPSPosition['lon'] = float(Fields[3])
                    self.GPSPosition['alt'] = float(Fields[4])

            self.GPSPosition['sats'] = int(Fields[5])
            if self._WhenNewPosition:
                self._WhenNewPosition(self.GPSPosition)
        elif Command == 'LORA':

            if self._WhenNewSentence:
                self._WhenNewSentence(Parameters)
        else:
            print("UNKOWN RESPONSE " + Command + '=' + Parameters)

    def ProcessLine(self, Line):
        
        # print(Line);
        if Line == '*':
            print(Line)
            self.CanSendNextCommand = True
        else:
            fields = Line.split('=', 2)
            
            if len(fields) == 2:
                self.ProcessCommand(fields[0], fields[1])
            else:
                print(Line)
                
    def AddCommand(self, Command):
        self.Commands.append(Command)
        
    def __comms_thread(self):
        print ("Comms thread")
        self.CanSendNextCommand = True
        Line = ''
        TimeOut = 0

        while True:
            if self.IsOpen:
                # Do incoming characters
                Byte = self.ser.read(1)
                
                if len(Byte) > 0:
                    Character = chr(Byte[0])

                    if len(Line) > 256:
                        Line = ''
                    elif Character != '\r':
                        if Character == '\n':
                            self.ProcessLine(Line)
                            
                            Line = ''
                            time.sleep(0.1)
                        else:
                            Line = Line + Character
                        
                if self.CanSendNextCommand or (TimeOut <= 0):
                    if len(self.Commands) > 0:
                        print("CAN SEND")
                        Command = '~' + self.Commands[0] + '\r\n'
                        print ('TX: ' + Command)
                        self.ser.write(Command.encode())
                        TimeOut = 2000
                        self.CanSendNextCommand = False
                        self.Commands = self.Commands[1:]
                
                if TimeOut > 0:
                    TimeOut -= 1
                        
            else:
                time.sleep(1)

    def open(self):
        # Open connection to FlexTrak board
        try:
            self.ser.open()
            self.IsOpen = True
            print ("AVR module connected")
        except:
            self.IsOpen = False
            print ("AVR module connection failed")
    
    def Position(self):
        return GPSPosition
                  
    @property
    def WhenLockGained(self):
        return self._WhenLockGained

    @WhenLockGained.setter
    def WhenLockGained(self, value):
        self._WhenLockGained = value
    
    @property
    def WhenLockLost(self):
        return self._WhenLockLost

    @WhenLockLost.setter
    def WhenLockGained(self, value):
        self._WhenLockLost = value
    
    @property
    def WhenNewSentence(self):
        return self._WhenNewSentence

    @WhenNewSentence.setter
    def WhenNewSentence(self, value):
        self._WhenNewSentence = value
    
    @property
    def WhenNewPosition(self):
        return self._WhenNewPosition

    @WhenNewPosition.setter
    def WhenNewPosition(self, value):
        self._WhenNewPosition = value
    
    def start(self):
        print ("Comms module started")
        self.open()
        t = threading.Thread(target=self.__comms_thread)
        t.daemon = True
        t.start()

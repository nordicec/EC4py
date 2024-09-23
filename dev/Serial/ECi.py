import serial
import codecs
import numpy as np

def start_potentiostat(port: str):
    ser = serial.Serial()
    ser.baudrate = 115200
    ser.port = port
    ser.timeout=1
    ser.open()
    ser
    ser.is_open
    return ser


class ECipot():
    def __init__(self):
        self.cell = 0
        self.IE = 0
        self.ini = 0
        self.cmode = 0
        self.ser = None
        
    def connect(self, port: str):
        self.ser = serial.Serial()
        self.ser.baudrate = 115200
        self.ser.port = port
        self.ser.timeout=1
        self.ser.open()
        self.ser
        if self.ser.is_open:
            for x in range(20):
                line = self.ser.readline(100)
                if line == b'Ini start\r\n':
                    break
                    
            for x in range(20):
                line = self.read_wait()
                if line is not None:
                    self.info(line)
                if line == b'Ini Done\r\n':
                    break
                print(line)
        self.ini = 1
        self.ser.readline(100)
        self.ser.readline(100)
        return self.ser

    def close(self):
        self.ser.close()
    
    def info(self, sline:str):
        #sline = str(line, encoding='utf-8')
        if sline[0:4] == "CELL":
            #sline = str(line[4:6], encoding='utf-8')
            s =sline[4:6]
            self.cell = int(s)
            print("CELL " + s)
        elif sline[0:5] == "CMODE":
            #sline = str(line[5:7], encoding='utf-8')
            s =sline[5:7]
            self.cmode = int(s)
            print("CMODE " + s)
        elif sline[0:2] == "IE":
            #sline = str(line[2:5], encoding='utf-8')
            s =sline[2:5]
            self.IE = int(s)
            print("IE " + s)
    ##############################################################
    def cell_on(self):
        if self.ser.is_open:
            self.ser.write(b"CELL 1\n")
    def cell_off(self):
        if self.ser.is_open:
            self.ser.write(b"CELL 0\n")
    
    def reads(self):
        line = None
        for x in range(1000):
            tline = self.read()
            if tline is None:
                break
            else:
                line = tline
        return line
    
    def read(self):
        line = None
        sline = None
        if self.ser.in_waiting > 0:
            line = self.ser.readline()
            self.info(line)
            sline = str(line, encoding='utf-8').rstrip()
            return sline
        else:
            return None
        
    def read_wait(self):
        line = self.ser.readline()
        sline = str(line, encoding='utf-8').rstrip()
        return sline
        
    def steps(self,t0,v0,t1= None,v1 = None,t2= None,v2 = None):
         if self.ser.is_open:
            string = f'step {t0} {v0}'
            if v1 is not None and t1 is not None:
                string = string + f' {t1} {v1}'
            if v2 is not None and t2 is not None:
                string = string + f' {t2} {v2}'
            string = string + "\n"
            b_string = codecs.encode(string, 'utf-8')
            print(b_string)
            self.ser.write(b_string) 
            for x in range(50):
                line = None
                line = self.read_wait()
                print(line)
                if line[0:3] == "INI":
                    break
            ##ini 
                
    
    def ramp(self,start:float,v1:float,v2:float,rate:float, nr):
        if self.ser.is_open:
            string = f'ramp {start} {v1} {v2} {rate} {nr}\n' 
            b_string = codecs.encode(string, 'utf-8')
            print(b_string)
            self.ser.write(b_string) 
            #pre init
            line = None
            for x in range(1000):
                line = None
                line = self.read_wait()
                if line[0:3] == "INI":
                    break
            ##ini 
            ini_data = np.empty([1000,3])
             
            print("INI: ", end ="")
         
            inidata = tempData()
            for x in range(1000):
                line = self.read_wait()
                if line[0:5] == "Start":
                    break
                else:
                    inidata.append(line)
                    print("x", end ="")
              
            print(" indexData",inidata.index)
            ##start
            ini_data = inidata.end()
            lastLine = inidata.lastLine
            print("start") 
            line = self.read()
            line = self.read()
            print(f"{line}0: ",end ="")
            line = self.read()
            #print(line)
            LSV  = []
            for lsv_nr in range(nr+2):
                tdata = tempData()
                tdata.append(lastLine)
                for x in range(2000):
                    
                    line = None
                    line = self.read_wait()
                    if line[0:9] == "change to":
                        print(f"\n{line}: ",end ="")
                        break
                    elif line[0:4] == "Done":
                        print("\nDone")
                        break
                    else:
                        tdata.append(line)
                        print("-", end ="")
                LSV.append(tdata.end())
                lastLine = tdata.lastLine
                if line[0:4] == "Done":
                    break            
            return LSV, ini_data




class tempData:
    def __init__(self):
        self.temp_data = np.empty([1000,3])
        self.index = 0
        self.lastLine = ""
        
    def append(self, line):
        if line[0:1] == "\t":
            self.lastLine = line
            data = line.split("\t")
            #print(data)
            self.temp_data[self.index,0] = float(data[1])
            self.temp_data[self.index,1] = float(data[2])
            self.temp_data[self.index,2] = float(data[3])
            self.index = self.index + 1
    
    def end(self):
        return np.resize(self.temp_data,(self.index,3))        
    

def line2data(line):
    if line[0:1] == "\t":
        data = line.split("\t")
        #print(data)
        return data
""" DRUGI DOMACI IZ PMS-A - Ulazak u banku
    Radili: Nikola Stojanovic 2020/0018
            Anastasija Rakic  2020/0030
"""

import sys
import time
from PyQt5.QtCore import QObject, QThread, pyqtSignal, Qt
from PyQt5.QtWidgets import *

import numpy as np
import serial 
from threading import Thread   

com_port = 'COM3'
baud_rate = 9600
ser = serial.Serial(com_port, baud_rate)

datoteka = open('IDbaza.txt','r')
upis = open('provalnik.txt', 'w')

poslednje = 0
sifra = "0000"
N = "0"
ID_tren = ""
svi_izasli = 0

"""ID броjеве непознатих картица jе потребно уписати у нову текстуалну датотеку
provalnik.txt заjедно са временом покушаjа неодобреног приступа."""
def upis_u_datoteku(provalnik):
    global poslednje
    trenutno = time.strftime("%H:%M:%S", time.localtime())
    trenutno_sec = int(round(time.time()))
    if((trenutno_sec - poslednje > 5) or (poslednje == 0)):
        upis.write(provalnik + '     ' + trenutno + '\n')
        poslednje = trenutno_sec
     
#Worker    
class Ocitavanje(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(str, str)
        
    def run(self):
        global N
        while(True): # Simulacija akvizicije
            try:
                global ID_tren
                time.sleep(0.1)
                datoteka.seek(0, 0)
                arduinoValue = ser.readline()
                vrednost = arduinoValue.decode()
                
                [N, ID, ocitana] =  vrednost.split(",")
                ID = ID[:-1]
    
                if(ocitana[:-2] == "1"):
                    ID_tren = ID[:-1]
                    i = False
                    # Уколико се ID налази у бази,прва врата се отвараjу.
                    for d in datoteka:
                        if (d == ID_tren):
                            i = True
                            
                    if(i == True):
                        op = 'OK\n'
                    else:
                        op = 'ALARM\n'
                        upis_u_datoteku(ID_tren)
              
                else:
                    op = '\n'
                salji = op + str(svi_izasli) + '\n'
                ser.write(salji.encode())
                self.progress.emit(ID_tren, N)
            except:
                continue
            
        self.finished.emit()
        ser.close()
        exit()

class App(QMainWindow):
    
    def __init__(self):
        super().__init__()
        self.title = 'Drugi domaci iz PMS-a'
        self.rt = True
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle(self.title)
        self.resize(500, 250)
        
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)
        
          
        # Dodavanje polja za prikaz ID ocitane karte
        self.prikaz_ID = QLabel('ID: ', self)
        self.prikaz_ID.setAlignment(Qt.AlignCenter)
        
        # Dodavanje polja za prikaz broja ljudi u banci
        self.br_ljudi = QLabel('Broj ljudi: 0', self)
        self.br_ljudi.setAlignment(Qt.AlignCenter)
        
        # Dodavanje polja za unos koda za izlazak iz banke
        self.kod = QLabel('Unesite cetvorocifren kod:', self)
        self.kod.setAlignment(Qt.AlignCenter)
        self.unos_koda = QLineEdit('', self)
        self.unos_koda.setAlignment(Qt.AlignCenter)
        
        # Taster IZLAZ za potvrdu izlaska
        self.dugmeIzlaz = QPushButton('IZLAZ', self)
        self.dugmeIzlaz.clicked.connect(self.izlaz)
      
        # Dodavanje polja za prikaz obavestenja
        self.prikaz_obavestenja = QLabel('', self)
        self.prikaz_obavestenja.setAlignment(Qt.AlignCenter)
      
        # Taster za iskljucivanje aplikacije
        self.dugmeIskljuci = QPushButton('ISKLJUCI', self)
        self.dugmeIskljuci.clicked.connect(self.iskljuci)
        
        layout = QVBoxLayout()
        
        layout.addWidget(self.prikaz_ID)
        layout.addWidget(self.br_ljudi)
        layout.addWidget(self.kod)
        layout.addWidget(self.unos_koda)
        layout.addWidget(self.dugmeIzlaz)
        layout.addWidget(self.prikaz_obavestenja)
        layout.addWidget(self.dugmeIskljuci)
        self.centralWidget.setLayout(layout)
        
        self.citanjeIDa()
    
    """Из банке се излази помоћу четвороцифреног кода коjи се добиjа 
    приликом завршетка трансакциjе. Притиском на тастер ИЗЛАЗ коjи се 
    налази на корисничком интерфеjсу сепроверава да ли jе унети код исправан."""
    def izlaz(self):
        global sifra, svi_izasli, N
        A = self.unos_koda.text()
        if(int(N) - svi_izasli <= 0):
            self.prikaz_obavestenja.setText("Duhovi?")
        elif(A == sifra):
            self.prikaz_obavestenja.setText("Molimo Vas napustite objekat.")
            i = int(sifra)+1
            sifra = f'{i:04d}'
            svi_izasli = svi_izasli + 1
        else:
            self.prikaz_obavestenja.setText("Niste uneli dobar kod, probajte ponovo!")
            
    def iskljuci(self):
        datoteka.close()
        upis.close()
        poy = 'KRAJ\n'
        ser.write(poy.encode())
        self.close()
        
        
    def reportProgress(self, n, N):
        self.worker.run_thread = self.rt # Zaustavljanje akvizicje
        self.prikaz_ID.setText("ID: " + n)
        if(N.isnumeric()):
            self.br_ljudi.setText('Broj ljudi: ' + str(int(N)-svi_izasli))
            
    def citanjeIDa(self):
        # Napraviti nit
        self.thread = QThread()
        
        # Napraviti objekat klase Worker
        self.worker = Ocitavanje()
        # Spajanje "radnika" sa niti
        self.worker.moveToThread(self.thread)
        
        # Povezati sve signale
        # Prvo se aktivira funkcija "run"
        self.thread.started.connect(self.worker.run)
        # Spaja se signal koji oznacava da je funkcija u thread-u gotova 
        # kako bi se thread obrisao
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        # Spaja se signal koji prenosi informacije tokom ozvrsavanja same 
        # funkcije unutar "radnika"
        self.worker.progress.connect(self.reportProgress)
        
        # Startovanje niti
        self.thread.start()
        

app = QApplication(sys.argv)
win = App()
win.show()
app.exec_()


    

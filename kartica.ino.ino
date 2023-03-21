#include <SPI.h>
#include <MFRC522.h>
#include <TM1637Display.h>
#include <TimerOne.h>

#define SS_PIN 10
#define RST_PIN 7

const int touchPin = 2;
const int ledPin = 3;
const int ledPinZ = 4;
const int trigPin = 5;
const int echoPin = 6;
const int DIO = 8; 
const int CLK = 9; 

volatile int voltage = 0; // napon potenciometra
volatile byte state = 0;
String inputString = "";
String ID = "";
long trajanje;
int rastojanje;

bool tu_je = false; // pomocna promenljiva za naznacavanje da li je neko u zastitnoj prostoriji
bool koji = false; // pomocna promenljiva za razdvajanje citanje ID-a i broja izaslih
bool ocitana = false; // da li je ocitana kartica

int N = 0;
int MAX;
int svi_izasli = 0;

TM1637Display display(CLK, DIO);
MFRC522 mfrc522(SS_PIN, RST_PIN);   // MFRC522 instanca

void setup()
{
  Serial.begin(9600);   // Inicijalizacija serijske komunikacije
  SPI.begin();      // SPI linija
  
  mfrc522.PCD_Init();   // Inicijalizacija MFRC522
 
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  pinMode(touchPin, INPUT_PULLUP);
  
  attachInterrupt(digitalPinToInterrupt(touchPin), pali, CHANGE);
  
  display.setBrightness(7);

  Timer1.initialize(100000);
  Timer1.attachInterrupt(timerIsr);

}

void serialEvent() 
{
  while (Serial.available()) 
  {
    char inChar = (char) Serial.read();
    if (inChar == '\n') {
      if(!koji)
      {
        ID = inputString;
        koji = true;
      }
      else
      {
        svi_izasli = inputString.toInt();
        koji = false;
      }
      inputString = "";
    }
    else 
    {
      inputString += inChar;
    }
  }
}

void loop()
{
  if(state)
  {
    state = 0;
  }
    
  MAX = 4 * floor(voltage/100); //Максималан броj људи у банци се контролише коришћењем потенциометра.
  
  //senzor daljine
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  
  trajanje = pulseIn(echoPin, HIGH);
  
  rastojanje = trajanje*0.034/2;

  // slanje informacija Pythonu
  String content = "";
  content.concat(N);
  content.concat(",");
  
  ocitana = 0;
  // Da li ima novih kartica i proverava da li je moguće pročitati ID kartice
  if (mfrc522.PICC_IsNewCardPresent() && mfrc522.PICC_ReadCardSerial() && (MAX > N - svi_izasli))
  {
     ocitana = 1;
     analogWrite(ledPinZ, 0); //Зелена лампица се искључуjе при следећем очитавању RFIDкартице. 
     //Prikaz ID
     for (byte i = 0; i < mfrc522.uid.size; i++)
       {
        content.concat(String(mfrc522.uid.uidByte[i], HEX));
        content.concat(" ");
       }
  }
  content.concat(" ,");
  content.concat(ocitana);
 
  Serial.println(content);

  if (ID == "OK") {
    analogWrite(ledPin, 0);
    tu_je = true;
  }
  if (ID == "ALARM") {
    analogWrite(ledPin, 200);
  }
  if (ID == "KRAJ"){
    analogWrite(ledPin, 0);
    analogWrite(ledPinZ, 0);
    display.showNumberDec(0);
  }
  else {
    display.showNumberDec(N - svi_izasli);
  }
}

void pali() 
{
  if(rastojanje <= 10 && tu_je) //Прва врата се сматраjу затвореним уколико jе растоjање коjе мери ултразвучни сензор мање од 10 cm. 
  {
    analogWrite(ledPinZ, 200);
    tu_je = false;
    N = N + 1;
  }
}

void timerIsr()
{
    state = 1;
    voltage = analogRead(A0);
}

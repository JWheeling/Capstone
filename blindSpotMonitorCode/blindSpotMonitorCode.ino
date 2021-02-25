//Sets up pin names and numbers
int ambientPin = A5;
int sensorPin1 = A4;
int sensorPin2 = A3;

int rightOnPin = 7;
int leftOnPin = 8;

//This pin is controlled externally and will indicate when the system needs to be set up
int setupModeDetectPin = 9;

/*Value used to determine the rate at which the blinker flashes
This will be different on every car
Will need to be figured out by a seperate program */
int carValue = 0;

//Used to fine tune how many flashes are needed before we turn on camera
int count = 0;
int minFlashes = 1;

//This is an experimental value that is yet to be determined
//Needs to be a number greater than 0
double errorFactor = .1;

//This value is set by an interrupt so that the program knows when the car value needs to be set
bool carValSetup = false;

//These variables are used to detect if the turn signal is currently on or was previously on
bool rightOn;
bool leftOn;

//This is a character buffer that will store the data from the serial port
char rxData[20];
char rxIndex=0;

//Variables to hold the speed and RPM data.
int vehicleSpeed=0;
int vehicleRPM=0;

//This function outputs based on which sensor is being activated
void turnOnBlindSpotCameras(){
  
  //Does logic for the right sensor
  if(rightOn && count >= minFlashes){
    digitalWrite(rightOnPin, HIGH);
  }else{
    digitalWrite(rightOnPin, LOW);
  }

  //Does logic for the left sensor
  if(leftOn && count >= minFlashes){
    digitalWrite(leftOnPin, HIGH);
  }else{
    digitalWrite(leftOnPin, LOW);
  }
}

void setup() {
  //Sets up the board
  pinMode(ambientPin, INPUT);
  pinMode(sensorPin1, INPUT);
  pinMode(sensorPin1, INPUT);
  pinMode(setupModeDetectPin, INPUT);
  pinMode(rightOnPin, OUTPUT);
  pinMode(leftOnPin, OUTPUT);

  //Sets initial values for the detection
  rightOn = false;
  leftOn = false;

  //Used to setup the serial monitor for testing
  Serial.begin(9600);

  //Reset the OBD-II-UART
  Serial.println("ATZ");
}

void loop() {
  
  //Reads in from the pins
  double ambientValue = analogRead(ambientPin);
  double sensorValue1 = analogRead(sensorPin1);
  double sensorValue2 = analogRead(sensorPin2);

  //Query the OBD-II-UART for the Vehicle Speed
  Serial.println("010D");
  //Get the response from the OBD-II-UART board. We get two responses
  //because the OBD-II-UART echoes the command that is sent.
  //We want the data in the second response.
  getResponse();
  getResponse();
  //Convert the string data to an integer
  vehicleSpeed = strtol(&rxData[6],0,16);
  
  //Prints values to the screen for testing
  Serial.print("Sensor Value 1: ");
  Serial.println(sensorValue1);
  Serial.print("Sensor Value 2: ");
  Serial.println(sensorValue2);
  Serial.print("Ambient Value: ");
  Serial.println(ambientValue);
  
  //Detects if the system needs to be setup
  if(digitalRead(setupModeDetectPin)){
    carValueSet();
  }

  //Detects if the right sensor is on
  if(sensorValue1 > ambientValue*(1+errorFactor)){
    count++;
    rightOn = true;
    delay(carValue);
  }else{
    rightOn = false;
  }
  
  //Detects if the left sensor is on
  if(sensorValue2 > ambientValue*(1+errorFactor)){
    count++;
    leftOn = true;
    delay(carValue);
  }else{
    leftOn = false;
  }

  //Does output accrding to the sensor values
  turnOnBlindSpotCameras();

  //Prints count to the screen for testing purposes
  Serial.print("Count: ");
  Serial.println(count);

}

void carValueSet(){

  while(digitalRead(setupModeDetectPin)){
    
    double startTime = millis();
    while(true){
      
    }
    double endTime = millis();
    carValue = endTime - startTime;
    
  }
}

//The getResponse function collects incoming data from the UART into the rxData buffer
// and only exits when a carriage return character is seen. Once the carriage return
// string is detected, the rxData buffer is null terminated (so we can treat it as a string)
// and the rxData index is reset to 0 so that the next string can be copied.
void getResponse(void){
  char inChar=0;
  //Keep reading characters until we get a carriage return
  while(inChar != '\r'){
    //If a character comes in on the serial port, we need to act on it.
    if(Serial.available() > 0){
      //Start by checking if we've received the end of message character ('\r').
      if(Serial.peek() == '\r'){
        //Clear the Serial buffer
        inChar=Serial.read();
        //Put the end of string character on our data string
        rxData[rxIndex]='\0';
        //Reset the buffer index so that the next character goes back at the beginning of the string.
        rxIndex=0;
      }
      //If we didn't get the end of message character, just add the new character to the string.
      else{
        //Get the new character from the Serial port.
        inChar = Serial.read();
        //Add the new character to the string, and increment the index variable.
        rxData[rxIndex++]=inChar;
      }
    }
  }
}

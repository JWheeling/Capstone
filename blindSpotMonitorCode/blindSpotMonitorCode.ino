//Sets up pin names and numbers
int ambientPin = A5;
int sensorPin1 = A4;
int sensorPin2 = A3;

int rightOnPin = 7;
int leftOnPin = 8;

//Used for testing
int testPin = 12;
bool currentVal = false;

//Sets up reset time before the camera turns back off
int blinkRate = 1200;
int blinkRateCounter = 0;

//Allows for error detection in light on logic
//minFlashes is not the actual number of flashes before it turns on
//minFlashes is the minimum on time
int minFlashes = 100;
int count = 0;

//This is an experimental value that is yet to be determined
//Needs to be a number greater than 0
double errorFactor = 1.5;

//This value is set by an interrupt so that the program knows when the car value needs to be set
bool carValSetup = false;

//These variables are used to detect if the turn signal is currently on or was previously on
bool rightOn;
bool leftOn;

//Allows for the clock divider fashion of quesrying the OBDII board
//1500 querys the board every .9048 Hz or 1.105 seconds
int queryRate = 2500;
int queryRateCounter = 0;

//This function outputs based on which sensor is being activated
void turnOnBlindSpotCameras(){
  
  //Does logic for the right sensor
  if(rightOn && (count >= minFlashes)){
    digitalWrite(rightOnPin, LOW);
  }else{
    digitalWrite(rightOnPin, HIGH);
  }

  //Does logic for the left sensor
  if(leftOn && (count >= minFlashes)){
    digitalWrite(leftOnPin, LOW);
  }else{
    digitalWrite(leftOnPin, HIGH);
  }
}

void setup() {
  //Sets up the board
  pinMode(ambientPin, INPUT);
  pinMode(sensorPin1, INPUT);
  pinMode(sensorPin1, INPUT);
  pinMode(rightOnPin, OUTPUT);
  pinMode(leftOnPin, OUTPUT);

  //Sets initial values for the detection
  rightOn = true;
  leftOn = true;

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
  if(queryRateCounter < queryRate){
  	queryRateCounter++;
  }else{
  	Serial.println("010D");
  	queryRateCounter = 0;
  }
  
  if(blinkRateCounter < blinkRate && (rightOn || leftOn)){
	  blinkRate++;
  }else{
	  blinkRateCounter = 0;
  }

  //Detects if the right sensor is on
  if(sensorValue1 > ambientValue*(1+errorFactor)){
    rightOn = true;
	count++;
  }
  
  //Detects if the left sensor is on
  if(sensorValue2 >	ambientValue*(1+errorFactor)){
    leftOn = true;
	count++;
  }

  //Does output accrding to the sensor values
  turnOnBlindSpotCameras();

}

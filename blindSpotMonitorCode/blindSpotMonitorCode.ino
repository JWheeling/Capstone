//Sets up pin names and numbers
int ambientPin = A5;
int sensorPin1 = A4;
int sensorPin2 = A3;

int rightOnPin = 7;
int leftOnPin = 8;

//This pin is controlled externally and will indicate when the system needs to be set up
int setupModeDetectPin = 10;

/*Value used to determine the rate at which the blinker flashes
This will be different on every car
Will need to be figured out by a seperate program */
int carValue = 0;

//Used to fine tune how many flashes are needed before we turn on camera
int count = 0;
int minFlashes = 1;

//This is an experimental value that is yet to be determined
//Needs to be a number greater than 0
double errorFactor = .5;

//This value is set by an interrupt so that the program knows when the car value needs to be set
bool carValSetup = false;

//These variables are used to detect if the turn signal is currently on or was previously on
bool rightOn;
bool leftOn;

//Allows for the clock divider fashion of quesrying the OBDII board
int queryRate = 10;
int queryRateCounter = 0;

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
  if(queryRateCounter < queryRate){
  	queryRateCounter++;
  }else{
  	Serial.println("010D");
  	queryRateCounter = 0;
  }
  	
    
  //Detects if the system needs to be setup
  if(digitalRead(setupModeDetectPin) == true){
    Serial.println("Setting up");
    Serial.println(digitalRead(setupModeDetectPin));
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
  if(sensorValue2 >	ambientValue*(1+errorFactor)){
    count++;
    leftOn = true;
    delay(carValue);
  }else{
    leftOn = false;
  }

  //Does output accrding to the sensor values
  turnOnBlindSpotCameras();

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

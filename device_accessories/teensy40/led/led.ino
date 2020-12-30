int led = 13;

void setup() {
  // put your setup code here, to run once:
  led = 13;
  pinMode(led, OUTPUT);
  digitalWrite(led, LOW);

  Serial.begin(38400);
}

void loop() {
  // put your main code here, to run repeatedly:
  while(1){
    while(Serial.available()>0){
      char cmd = 0;
      cmd = Serial.read();
      switch(cmd){
        case '1':
          digitalWrite(led, HIGH);
          Serial.println("LED turned on! 1/3");
          // Serial.println("LED turned on! 2/3");
          // Serial.println("LED turned on! 3/3");
          while(Serial.available()>0){
            Serial.read();
          }
          break;
        case '0':
          digitalWrite(led, LOW);
          Serial.println("LED turned off! 1/4");
          // Serial.println("LED turned off! 2/4");
          // Serial.println("LED turned off! 3/4");
          // Serial.println("LED turned off! 4/4");
          while(Serial.available()>0){
            Serial.read();
          }
          break; 
        default: 
          Serial.println("Invalid Command!");
      }
    }
  }

}

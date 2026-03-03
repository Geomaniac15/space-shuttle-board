#include <FastLED.h>

#define LED_PIN 33
#define NUM_LEDS 5
#define BRIGHTNESS 40
#define LAUNCH_PIN 13

bool lastLaunchState = HIGH;
bool launchTriggered = false;
bool vehicleSurvives = false;

CRGB leds[NUM_LEDS];

void idleAnimation() {
  for (int i = 0; i < NUM_LEDS; i++) {
    leds[i] = CRGB::Blue;
  }
  FastLED.show();
}

void runLaunchSequence() {
  for (int i = 0; i < NUM_LEDS; i++) {
    leds[i] = CRGB::Orange;
    FastLED.show();
    delay(200);
  }

  delay(500);

  for (int i = 0; i < NUM_LEDS; i++) {
    vehicleSurvives = random(0, 100) > 40; // 60% survival
    if (vehicleSurvives) {
      for (int i = 0; i < NUM_LEDS; i++) {
        leds[i] = CRGB::Green;
      }
    } else {
      for (int i = 0; i < NUM_LEDS; i++) {
        leds[i] = CRGB::Red;
      }
    }

    FastLED.show();
    delay(1000);
  }
}

void setup() {
  FastLED.addLeds<WS2812B, LED_PIN, GRB>(leds, NUM_LEDS);
  FastLED.setBrightness(BRIGHTNESS);
  pinMode(LAUNCH_PIN, INPUT_PULLUP);
  randomSeed(analogRead(34));
}

void loop() {
  bool currentState = digitalRead(LAUNCH_PIN);

  if (lastLaunchState == HIGH && currentState == LOW) {
    launchTriggered = true;
  }

  lastLaunchState = currentState;

  if (launchTriggered) {
    runLaunchSequence();
    launchTriggered = false;
  }

  idleAnimation();
}
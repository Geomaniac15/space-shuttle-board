#include <FastLED.h>

#define LED_PIN 33
#define NUM_LEDS 5
#define BRIGHTNESS 40
#define LAUNCH_PIN 13

bool lastLaunchState = HIGH;
bool launchTriggered = false;

CRGB leds[NUM_LEDS];

void setup() {
  FastLED.addLeds<WS2812B, LED_PIN, GRB>(leds, NUM_LEDS);
  FastLED.setBrightness(BRIGHTNESS);
  pinMode(LAUNCH_PIN, INPUT_PULLUP);
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
    leds[i] = CRGB::Red;
  }
  FastLED.show();

  delay(1000);
}
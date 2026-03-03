#include <FastLED.h>

constexpr uint8_t LED_PIN = 33;
constexpr uint8_t NUM_LEDS = 15;
constexpr uint8_t BRIGHTNESS = 40;
constexpr uint8_t LAUNCH_PIN = 13;

CRGB leds[NUM_LEDS];

int lastLaunchState = HIGH;
bool launchTriggered = false;
bool showingResult = false;

// ---- TEMPORARY INPUTS ----
int tempC = 15;              // Change to 0, 5, 10, 15 to test
bool overrideActive = false;

// ---- Compute Survival Percentage (0-100) ----
uint8_t computeSurvivalPercent(int temp, bool overrideFlag) {
  int survival = 90; // percent

  if (temp <= 0) survival -= 40;
  else if (temp <= 5) survival -= 25;
  else if (temp <= 10) survival -= 10;

  if (overrideFlag) survival -= 15;

  survival = constrain(survival, 0, 100);
  return static_cast<uint8_t>(survival);
}

// ---- Idle State ----
void idleAnimation() {
  fill_solid(leds, NUM_LEDS, CRGB::Blue);
  FastLED.show();
}

// ---- Launch Sequence ----
void runLaunchSequence() {
  // Countdown sweep (builds up orange bar)
  for (uint8_t i = 0; i < NUM_LEDS; ++i) {
    leds[i] = CRGB::Orange;
    FastLED.show();
    delay(120);
  }

  delay(400);

  // Compute probability as integer percent
  uint8_t survivalPct = computeSurvivalPercent(tempC, overrideActive);

  // Visual probability bar (number of green LEDs)
  uint8_t litCount = (survivalPct * NUM_LEDS + 99) / 100;
  for (uint8_t i = 0; i < NUM_LEDS; ++i) {
    leds[i] = (i < litCount) ? CRGB::Green : CRGB::Black;
  }
  FastLED.show();
  delay(1200);

  // Random roll using integer percent
  bool vehicleSurvives = (static_cast<uint8_t>(random(100)) < survivalPct);

  if (vehicleSurvives) {

    // Success → whole strip turns green
    fill_solid(leds, NUM_LEDS, CRGB::Green);
    FastLED.show();

  } else {

    // Failure → red cascade across strip
    for (uint8_t i = 0; i < NUM_LEDS; ++i) {
      leds[i] = CRGB::Red;
      FastLED.show();
      delay(80);
    }

  }

  delay(2000);
  showingResult = true;
}

void setup() {
  FastLED.addLeds<WS2812B, LED_PIN, GRB>(leds, NUM_LEDS);
  FastLED.setBrightness(BRIGHTNESS);

  pinMode(LAUNCH_PIN, INPUT_PULLUP);

  randomSeed(analogRead(34));
}

void loop() {
  int currentState = digitalRead(LAUNCH_PIN);

  // Edge detect: HIGH -> LOW
  if (lastLaunchState == HIGH && currentState == LOW) {
    launchTriggered = true;
    showingResult = false;
  }
  lastLaunchState = currentState;

  if (launchTriggered) {
    runLaunchSequence();
    launchTriggered = false;
  }

  if (!showingResult) {
    idleAnimation();
  }  
}
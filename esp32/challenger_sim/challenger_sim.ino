// =============================================================
// Space Shuttle Challenger - Cascade Failure Simulator
// ESP32 + WS2812B (20 LEDs) + Rotary Encoder (temp + override)
//
// Encoder twist  -> temperature (-5 to +20 C, 1 degree per click)
// Encoder press  -> toggle override on/off
//
// LED_MAP[] remaps logical node IDs to physical
// LED positions so the wiring order matches the poster.
// =============================================================

#include <FastLED.h>

// --- Hardware ---
#define LED_PIN       5
#define NUM_LEDS      20
#define BRIGHTNESS    70
#define LED_TYPE      WS2812B
#define COLOR_ORDER   GRB

#define ENC_CLK       18
#define ENC_DT        19
#define ENC_SW        21

// --- Sim ---
#define SIM_STEPS        60
#define STEP_DELAY_MS    80
#define END_PAUSE_MS     2500
#define TEMP_MIN        -5.0f
#define TEMP_MAX        20.0f

// =============================================================
// Node IDs (logical, not physical wiring order)
// =============================================================
enum NodeID {
  // SRB chain
  N_FIELD_JOINT = 0,
  N_JOINT_ROT,
  N_PRIMARY_SEAL,
  N_SECONDARY_SEAL,
  N_BLOWBY,
  N_FLAME,
  // Tank + structure
  N_EXT_TANK,
  N_LH2_BREACH,
  N_LOAD_DIST,
  N_SURVIVAL,
  N_INTERTANK,
  // Aero + control
  N_ICE_RISK,
  N_AERO_STRESS,
  N_FCS,
  N_POWER,
  // Context / exogenous
  N_PRESSURE,
  N_SENSOR,
  N_SRB_TEMP,
  N_SRB_CASE,
  N_AMBIENT,
  NUM_NODES
};

// =============================================================
// LED_MAP[logical_node_id] = physical index on the LED strip.
// Default is 1:1. Change to match your wiring order on the poster.
// =============================================================
const uint8_t LED_MAP[NUM_NODES] = {
  0,   // N_FIELD_JOINT
  1,   // N_JOINT_ROT
  2,   // N_PRIMARY_SEAL
  3,   // N_SECONDARY_SEAL
  4,   // N_BLOWBY
  5,   // N_FLAME
  6,   // N_EXT_TANK
  7,   // N_LH2_BREACH
  8,   // N_LOAD_DIST
  9,   // N_SURVIVAL
  10,  // N_INTERTANK
  11,  // N_ICE_RISK
  12,  // N_AERO_STRESS
  13,  // N_FCS
  14,  // N_POWER
  15,  // N_PRESSURE
  16,  // N_SENSOR
  17,  // N_SRB_TEMP
  18,  // N_SRB_CASE
  19,  // N_AMBIENT
};

// SRB corridor: override active worsens failure probability here
const bool SRB_CORRIDOR[NUM_NODES] = {
  true,  // N_FIELD_JOINT
  true,  // N_JOINT_ROT
  true,  // N_PRIMARY_SEAL
  true,  // N_SECONDARY_SEAL
  true,  // N_BLOWBY
  true,  // N_FLAME
  false, false, false, false, false,
  false, false, false, false,
  false, false, false, false, false
};

// =============================================================
// State
// =============================================================
float node_health[NUM_NODES];
bool  node_failed[NUM_NODES];
bool  node_ov_active[NUM_NODES];

float temp_c      = 15.0f;
bool  do_override = false;
int   sim_step    = 0;
bool  sim_running = false;

int  enc_clk_prev;
bool btn_prev = HIGH;

CRGB leds[NUM_LEDS];

// =============================================================
// Helpers
// =============================================================
float sigmoid_f(float x) {
  if (x >  20.0f) return 1.0f;
  if (x < -20.0f) return 0.0f;
  return 1.0f / (1.0f + expf(-x));
}

float rand01() {
  return (float)random(100000) / 100000.0f;
}

// =============================================================
// Simulation - direct port of simulator.py update_system()
// =============================================================
void reset_sim() {
  for (int i = 0; i < NUM_NODES; i++) {
    node_health[i]    = 1.0f;
    node_failed[i]    = false;
    node_ov_active[i] = false;
  }
  sim_step = 0;
}

void update_exogenous(int t) {
  node_health[N_AMBIENT]   = constrain(temp_c / 15.0f, 0.0f, 1.0f);
  node_health[N_ICE_RISK]  = 1.0f - sigmoid_f((5.0f - temp_c) * 1.0f);
  node_health[N_SENSOR]    = max(0.0f, 1.0f - 0.02f * max(0.0f, 10.0f - temp_c));
  node_health[N_SRB_TEMP]  = max(0.0f, 1.0f - 0.03f * max(0.0f, 10.0f - temp_c));
  node_health[N_SRB_CASE]  = 1.0f;
  node_health[N_INTERTANK] = 1.0f;

  float pressure          = sigmoid_f((t - 8) * 0.7f);
  node_health[N_PRESSURE] = 1.0f - 0.6f * pressure;
  node_health[N_POWER]    = max(0.0f, (1.0f - 0.01f * pressure) - 0.03f * rand01());
}

// Process one endogenous node.
// deps[] and n_deps must exactly mirror NODE_DEPS in simulator.py.
void process_node(int idx, const int* deps, int n_deps) {
  if (node_failed[idx]) return;

  node_ov_active[idx] = (do_override && SRB_CORRIDOR[idx]);

  float stress = 0.0f;
  bool  any_dep_failed = false;
  for (int i = 0; i < n_deps; i++) {
    stress += (1.0f - node_health[deps[i]]);
    if (node_failed[deps[i]]) any_dep_failed = true;
  }

  // Structural Load Distribution: extra weight from aerodynamic stress
  if (idx == N_LOAD_DIST) {
    stress += 2.0f * (1.0f - node_health[N_AERO_STRESS]);
  }

  // Aerodynamic Stress self-degrades slowly, floored at 0.8
  if (idx == N_AERO_STRESS) {
    node_health[idx] = max(0.8f, node_health[idx] * 0.98f);
  }

  // Propagation shock when a parent has already failed
  if (any_dep_failed) {
    float shock = 1.5f + rand01() * 1.5f;  // matches random.uniform(1.5, 3.0)
    if (do_override && SRB_CORRIDOR[idx] && temp_c < 7.0f) shock += 0.5f;
    stress += shock;
    node_health[idx] *= 0.85f;
  }

  // Override adds direct stress inside SRB corridor
  if (do_override && SRB_CORRIDOR[idx]) stress += 0.5f;

  // Field Joint baseline shifts with cold - the key Challenger mechanic
  float baseline = -10.0f;
  if (idx == N_FIELD_JOINT && temp_c < 10.0f) {
    baseline = -9.5f + 0.2f * (10.0f - temp_c);
  }

  float p_fail = sigmoid_f(baseline + 2.5f * stress);

  if (rand01() < p_fail) {
    node_failed[idx]  = true;
    node_health[idx]  = 0.0f;
  } else {
    node_health[idx] = max(0.1f, node_health[idx] * (1.0f - 0.01f * stress));
  }
}

void update_endogenous() {
  // Strict topological order matching NODE_DEPS in simulator.py
  const int d_fj[] = {N_AMBIENT, N_PRESSURE};              process_node(N_FIELD_JOINT,    d_fj, 2);
  const int d_jr[] = {N_FIELD_JOINT, N_SRB_TEMP};          process_node(N_JOINT_ROT,      d_jr, 2);
  const int d_ps[] = {N_JOINT_ROT};                        process_node(N_PRIMARY_SEAL,   d_ps, 1);
  const int d_ss[] = {N_PRIMARY_SEAL};                     process_node(N_SECONDARY_SEAL, d_ss, 1);
  const int d_bb[] = {N_SECONDARY_SEAL, N_SRB_CASE};       process_node(N_BLOWBY,         d_bb, 2);
  const int d_fl[] = {N_BLOWBY};                           process_node(N_FLAME,          d_fl, 1);
  const int d_et[] = {N_FLAME};                            process_node(N_EXT_TANK,       d_et, 1);
  const int d_lh[] = {N_EXT_TANK};                         process_node(N_LH2_BREACH,     d_lh, 1);
  const int d_fc[] = {N_POWER};                            process_node(N_FCS,            d_fc, 1);
  const int d_as[] = {N_FCS, N_ICE_RISK};                  process_node(N_AERO_STRESS,    d_as, 2);
  const int d_ld[] = {N_LH2_BREACH, N_INTERTANK, N_AERO_STRESS}; process_node(N_LOAD_DIST, d_ld, 3);
  const int d_sv[] = {N_LOAD_DIST};                        process_node(N_SURVIVAL,       d_sv, 1);
}

void update_system(int t) {
  for (int i = 0; i < NUM_NODES; i++) node_ov_active[i] = false;
  update_exogenous(t);
  update_endogenous();
}

// =============================================================
// LED colours - matching visualisation.py palette
// =============================================================
CRGB node_colour(int idx) {
  if (node_failed[idx]) {
    // pulsing red ~6 Hz
    uint8_t p = 150 + (uint8_t)(50.0f * sinf((float)millis() * 0.006f));
    return CRGB(p, 0, 0);
  }

  CRGB base = (node_health[idx] < 0.6f)
    ? CRGB(255, 140, 0)    // orange: stressed
    : CRGB(140, 180, 230); // blue:   healthy

  if (node_ov_active[idx]) {
    // purple pulse ~4 Hz on top of base colour
    int p = (int)(20.0f * sinf((float)millis() * 0.004f));
    base.r = (uint8_t)min(255, (int)base.r + 100 + p);
    base.b = (uint8_t)min(255, (int)base.b + 100 + p);
  }

  return base;
}

void show_leds() {
  for (int i = 0; i < NUM_NODES; i++) {
    leds[LED_MAP[i]] = node_colour(i);
  }
  FastLED.show();
}

void victory_flash() {
  for (int f = 0; f < 3; f++) {
    fill_solid(leds, NUM_LEDS, CRGB(0, 200, 80));
    FastLED.show(); delay(300);
    fill_solid(leds, NUM_LEDS, CRGB::Black);
    FastLED.show(); delay(200);
  }
}

void failure_flash() {
  for (int f = 0; f < 5; f++) {
    fill_solid(leds, NUM_LEDS, CRGB(220, 0, 0));
    FastLED.show(); delay(200);
    fill_solid(leds, NUM_LEDS, CRGB::Black);
    FastLED.show(); delay(150);
  }
}

// =============================================================
// Rotary encoder
// =============================================================
void read_encoder() {
  int clk = digitalRead(ENC_CLK);
  if (clk != enc_clk_prev && clk == LOW) {
    if (digitalRead(ENC_DT) != clk) {
      temp_c = min(TEMP_MAX, temp_c + 1.0f);
    } else {
      temp_c = max(TEMP_MIN, temp_c - 1.0f);
    }
    Serial.print(F('Temp: ')); Serial.print((int)temp_c); Serial.println(F('C'));
  }
  enc_clk_prev = clk;

  bool btn = digitalRead(ENC_SW);
  if (btn == LOW && btn_prev == HIGH) {
    do_override = !do_override;
    Serial.print(F('Override: ')); Serial.println(do_override ? F('ON') : F('OFF'));
    delay(50); // debounce
  }
  btn_prev = btn;
}

// =============================================================
// Setup & loop
// =============================================================
void setup() {
  Serial.begin(115200);

  FastLED.addLeds<LED_TYPE, LED_PIN, COLOR_ORDER>(leds, NUM_LEDS);
  FastLED.setBrightness(BRIGHTNESS);
  fill_solid(leds, NUM_LEDS, CRGB::Black);
  FastLED.show();

  pinMode(ENC_CLK, INPUT_PULLUP);
  pinMode(ENC_DT,  INPUT_PULLUP);
  pinMode(ENC_SW,  INPUT_PULLUP);
  enc_clk_prev = digitalRead(ENC_CLK);

  randomSeed(analogRead(0));  // seed from floating ADC pin for real randomness

  reset_sim();
  sim_running = true;

  Serial.println(F('=== Challenger Simulator Ready ==='));
  Serial.println(F('Twist: temperature | Press: toggle override'));
}

void loop() {
  read_encoder();

  if (!sim_running) {
    delay(END_PAUSE_MS);
    reset_sim();
    sim_running = true;
    return;
  }

  if (sim_step < SIM_STEPS && !node_failed[N_SURVIVAL]) {
    update_system(sim_step);
    show_leds();
    sim_step++;
    delay(STEP_DELAY_MS);
  } else {
    sim_running = false;
    if (node_failed[N_SURVIVAL]) {
      failure_flash();
      Serial.println(F('--- LOSS OF VEHICLE ---'));
    } else {
      victory_flash();
      Serial.println(F('--- MISSION SUCCESS ---'));
    }
  }
}

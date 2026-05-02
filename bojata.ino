// Nano 33 BLE
#include <mbed_chrono.h>
#include <platform/Callback.h>
#include <rtos.h>

using namespace std::literals::chrono_literals;

#ifndef DEBUG
#   define DEBUG 0
#endif

#ifndef TFT_SCREEN
#   define TFT_SCREEN 0
#endif
#if TFT_SCREEN
#   include <TFT_ILI9163C.h>
#endif

#ifndef PRINT_BUTTON
#   define PRINT_BUTTON 0
#endif

#define BAUD_RATE   115200UL
#define MAIN_DELAY  300ms
#define TFT_DELAY   0ms
#define PRINT_DELAY 1ms

#if PRINT_BUTTON
#   define PRINT_FLAG "@"
#   define PRINT_PIN  8
#endif

// TCS230 color sensor pins
#define SENSOR_S0  3
#define SENSOR_S1  4
#define SENSOR_S2  5
#define SENSOR_S3  6
#define SENSOR_OUT 7

// Color frequency bounds
#define R_MIN 5000  //  600  3000  5000
#define R_MAX 1000  //   80  1200  1000
#define G_MIN 6000  //  750  4000  6000
#define G_MAX 1500  //   80  1200  1500
#define B_MIN 5000  //  600  3000  5000
#define B_MAX 1000  //   80  1200  1000

#if TFT_SCREEN
// TFT_ILI9163C screen pins (+ SCLK, MOSI)
#   define TFT_A0 9
#   define TFT_CS 10

#   define TFT_BLACK 0x0000
#   define TFT_BLUE  0x001F
#   define TFT_GREEN 0x07E0
#   define TFT_RED   0xF800
#   define TFT_WHITE 0xFFFF

inline uint16_t toRgb565(uint8_t r8, uint8_t g8, uint8_t b8) {
    return ((r8 & 0xF8) << 8) | ((g8 & 0xFC) << 3) | ((b8 & 0xF8) >> 3);
}

TFT_ILI9163C tft = TFT_ILI9163C(TFT_CS, TFT_A0);

rtos::Thread tftThread;
rtos::Semaphore tftSem(0, 1);
uint16_t tftColor;

void paintScreen() {
    while (true) {
        // Paint TFT screen with 16-bit RGB565 value
        tftSem.acquire();
        tft.fillRect(0, 0, 128, 112, tftColor);

        rtos::ThisThread::sleep_for(TFT_DELAY);
    }
}
#endif

#if PRINT_BUTTON
rtos::Thread printThread;
rtos::Mutex printMutex;
bool printPressed;

void checkPrint() {
    static bool oldPrintState = HIGH;

    while (true) {
        bool printState = digitalRead(PRINT_PIN);
        if (printState != oldPrintState) {
            if (printState == LOW) {
                printMutex.lock();
                printPressed = true;
                printMutex.unlock();
            }
            oldPrintState = printState;
        }

        rtos::ThisThread::sleep_for(PRINT_DELAY);
    }
}
#endif

void setup() {
    pinMode(SENSOR_S0, OUTPUT);
    pinMode(SENSOR_S1, OUTPUT);
    pinMode(SENSOR_S2, OUTPUT);
    pinMode(SENSOR_S3, OUTPUT);
    pinMode(SENSOR_OUT, INPUT);

    // Set frequency scaling to 20%
    digitalWrite(SENSOR_S0, HIGH);
    digitalWrite(SENSOR_S1, LOW);

    Serial.begin(BAUD_RATE);

#if TFT_SCREEN
    tft.begin();
    tft.fillRect(86, 112, 43, 16, TFT_BLUE);
    tft.fillRect(43, 112, 43, 16, TFT_GREEN);
    tft.fillRect(0,  112, 43, 16, TFT_RED);

    // Paint TFT screen in a thread
    tftThread.start(mbed::callback(paintScreen));
#endif

#if PRINT_BUTTON
    pinMode(PRINT_PIN, INPUT_PULLUP);

    // Update print button state in a thread
    printThread.start(mbed::callback(checkPrint));
#endif
}

void loop() {
    int freq;
    uint8_t r8, g8, b8;
#if TFT_SCREEN
    uint8_t r5, g6, b5;
#endif

    // Set red filtered photodiodes to be read
    digitalWrite(SENSOR_S2, LOW);
    digitalWrite(SENSOR_S3, LOW);
    // Read output frequency
    freq = pulseIn(SENSOR_OUT, LOW);
#if DEBUG
    Serial.print(freq); Serial.print(" ");
#endif
    // Remap frequency to RGB888 and RGB565 ranges
    r8 = constrain(map(freq, R_MIN, R_MAX, 0, 255), 0, 255);
#if TFT_SCREEN
    r5 = constrain(map(freq, R_MIN, R_MAX, 0,  31), 0,  31);
#endif

    // Set green filtered photodiodes to be read
    digitalWrite(SENSOR_S2, HIGH);
    digitalWrite(SENSOR_S3, HIGH);
    // Read output frequency
    freq = pulseIn(SENSOR_OUT, LOW);
#if DEBUG
    Serial.print(freq); Serial.print(" ");
#endif
    // Remap frequency to RGB888 and RGB565 ranges
    g8 = constrain(map(freq, G_MIN, G_MAX, 0, 255), 0, 255);
#if TFT_SCREEN
    g6 = constrain(map(freq, G_MIN, G_MAX, 0,  63), 0,  63);
#endif

    // Set blue filtered photodiodes to be read
    digitalWrite(SENSOR_S2, LOW);
    digitalWrite(SENSOR_S3, HIGH);
    // Read output frequency
    freq = pulseIn(SENSOR_OUT, LOW);
#if DEBUG
    Serial.print(freq); Serial.println(" ");
#endif
    // Remap frequency to RGB888 and RGB565 ranges
    b8 = constrain(map(freq, B_MIN, B_MAX, 0, 255), 0, 255);
#if TFT_SCREEN
    b5 = constrain(map(freq, B_MIN, B_MAX, 0,  31), 0,  31);
#endif

    // Format 24-bit RGB888 value as string
    char rgb888[14];
    snprintf(rgb888, sizeof(rgb888)-2, "%d,%d,%d", r8, g8, b8);
#if PRINT_BUTTON
    // If print button was pressed, append print flag
    if (printPressed) {
        printMutex.lock();
        printPressed = false;
        printMutex.unlock();
        strcat(rgb888, PRINT_FLAG);
    }
#endif
    // Send RGB888 value (and potentially print flag) over serial
    Serial.println(rgb888);

#if TFT_SCREEN
    // Set RGB565 value used to paint the TFT screen
    tftColor = (r5 << 11) | (g6 << 5) | b5;
#   if DEBUG
    Serial.println(tftColor, HEX);
#   endif
    tftSem.release();
#endif

    rtos::ThisThread::sleep_for(MAIN_DELAY);
    Serial.flush();
}

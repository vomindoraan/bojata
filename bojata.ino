#include <platform/Callback.h>
#include <rtos.h>
#include <TFT_ILI9163C.h>

#define BAUD_RATE  115200

#define PRINT_PIN  8
#define PRINT_FLAG "@"

// TCS230 constants
#define SENSOR_S0  3
#define SENSOR_S1  4
#define SENSOR_S2  5
#define SENSOR_S3  6
#define SENSOR_OUT 7

// Galerija Reflektor, Užice
// #define R_MIN 600
// #define R_MAX 80
// #define G_MIN 750
// #define G_MAX 80
// #define B_MIN 600
// #define B_MAX 80

// Kulturni distrikt, Novi Sad
// #define R_MIN 3000
// #define R_MAX 1200
// #define G_MIN 4000
// #define G_MAX 1200
// #define B_MIN 3000
// #define B_MAX 1200

// Mercator Hipermarket, Novi Sad
#define R_MIN 5000
#define R_MAX 1000
#define G_MIN 6000
#define G_MAX 1500
#define B_MIN 5000
#define B_MAX 1000

// TFT_ILI9163C constants
#define TFT_A0 9
#define TFT_CS 10

#define BLACK 0x0000
#define BLUE  0x001F
#define RED   0xF800
#define GREEN 0x07E0
#define WHITE 0xFFFF

inline uint16_t toRgb565(uint8_t r8, uint8_t g8, uint8_t b8) {
    return ((r8 & 0xF8) << 8) | ((g8 & 0xFC) << 3) | ((b8 & 0xF8) >> 3);
}

#define TFT_DELAY   0
#define PRINT_DELAY 1
#define MAIN_DELAY  300

TFT_ILI9163C tft = TFT_ILI9163C(TFT_CS, TFT_A0);

rtos::Thread tftThread;
rtos::Semaphore tftSem(0, 1);
uint16_t tftRgb565;

rtos::Thread printThread;
rtos::Mutex printMutex;
bool printPressed;

void paintScreen() {
    while (true) {
        // Paint TFT screen with 16-bit RGB565 value
        tftSem.acquire();
        tft.fillRect(0, 0, 128, 112, tftRgb565);

        rtos::ThisThread::sleep_for(TFT_DELAY);
    }
}

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

void setup() {
    pinMode(PRINT_PIN, INPUT_PULLUP);

    pinMode(SENSOR_S0, OUTPUT);
    pinMode(SENSOR_S1, OUTPUT);
    pinMode(SENSOR_S2, OUTPUT);
    pinMode(SENSOR_S3, OUTPUT);
    pinMode(SENSOR_OUT, INPUT);

    // Set frequency scaling to 20%
    digitalWrite(SENSOR_S0, HIGH);
    digitalWrite(SENSOR_S1, LOW);

    Serial.begin(BAUD_RATE);

    tft.begin();
    tft.fillRect(86, 112, 43, 16, BLUE);
    tft.fillRect(43, 112, 43, 16, GREEN);
    tft.fillRect(0,  112, 43, 16, RED);

    // Paint TFT screen in a thread
    tftThread.start(mbed::callback(paintScreen));

    // Update print button state in a thread
    printThread.start(mbed::callback(checkPrint));
}

void loop() {
    int freq;
    uint8_t r8, g8, b8, r5, g6, b5;

    // Set red filtered photodiodes to be read
    digitalWrite(SENSOR_S2, LOW);
    digitalWrite(SENSOR_S3, LOW);
    // Read output frequency
    freq = pulseIn(SENSOR_OUT, LOW);
//    Serial.print(freq);
//    Serial.print(" ");
    // Remap frequency to RGB888 and RGB565 ranges
    r8 = constrain(map(freq, R_MIN, R_MAX, 0, 255), 0, 255);
    r5 = constrain(map(freq, R_MIN, R_MAX, 0,  31), 0,  31);

    // Set green filtered photodiodes to be read
    digitalWrite(SENSOR_S2, HIGH);
    digitalWrite(SENSOR_S3, HIGH);
    // Read output frequency
    freq = pulseIn(SENSOR_OUT, LOW);
//    Serial.print(freq);
//    Serial.print(" ");
    // Remap frequency to RGB888 and RGB565 ranges
    g8 = constrain(map(freq, G_MIN, G_MAX, 0, 255), 0, 255);
    g6 = constrain(map(freq, G_MIN, G_MAX, 0,  63), 0,  63);

    // Set blue filtered photodiodes to be read
    digitalWrite(SENSOR_S2, LOW);
    digitalWrite(SENSOR_S3, HIGH);
    // Read output frequency
    freq = pulseIn(SENSOR_OUT, LOW);
//    Serial.print(freq);
//    Serial.println(" ");
    // Remap frequency to RGB888 and RGB565 ranges
    b8 = constrain(map(freq, B_MIN, B_MAX, 0, 255), 0, 255);
    b5 = constrain(map(freq, B_MIN, B_MAX, 0,  31), 0,  31);

    // Format 24-bit RGB888 value as string
    char rgb888[13];
    snprintf(rgb888, 12, "%d,%d,%d", r8, g8, b8);
    // If print button was pressed, append print flag
    if (printPressed) {
        printMutex.lock();
        printPressed = false;
        printMutex.unlock();
        strcat(rgb888, PRINT_FLAG);
    }
    // Send RGB888 value and (potentially) print flag over serial
    Serial.println(rgb888);

    // Set RGB565 value used to paint the TFT screen
    tftRgb565 = (r5 << 11) | (g6 << 5) | b5;
//    Serial.println(rgb565, HEX);
    tftSem.release();

    rtos::ThisThread::sleep_for(MAIN_DELAY);
    Serial.flush();
}

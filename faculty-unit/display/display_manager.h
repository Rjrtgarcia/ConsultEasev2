#ifndef DISPLAY_MANAGER_H
#define DISPLAY_MANAGER_H

#include <SPI.h>             // Required for SPI communication
#include <Adafruit_GFX.h>    // Core graphics library
#include <Adafruit_ILI9341.h> // Hardware-specific library for ILI9341

// Include config.h to get pin definitions and screen dimensions
#include "../config/config.h"

/**
 * @brief Static utility class for managing the ILI9341 TFT display.
 * Provides methods for initialization and drawing status/request information.
 */
class DisplayManager {
public:
    // Constructor is not needed for a static class
    // DisplayManager();

    /**
     * @brief Initializes the TFT display object and clears the screen.
     * @return true if initialization is successful, false otherwise.
     */
    static bool setup_display();

    /**
     * @brief Clears the entire display area.
     */
    static void clear_display();

    /**
     * @brief Displays the faculty's current status (e.g., "Present", "Unavailable")
     *        in a designated area of the screen.
     * @param status_text The status string to display.
     */
    static void show_status(const char* status_text);

    /**
     * @brief Displays details of an incoming consultation request
     *        (Student ID, Request Text) in a designated area.
     * @param student_id The ID of the student making the request.
     * @param request_text The text of the consultation request.
     */
    static void show_request(const char* student_id, const char* request_text);

    /**
     * @brief Placeholder/Compatibility function. For ILI9341 with Adafruit_GFX,
     *        drawing commands often update the display directly. This might not be needed.
     */
    static void update_display();

private:
    // Private members are not needed for this purely static utility class
    // unless managing internal static state.
};

// Function-based approach (alternative to class)
// void setup_display();
// void clear_display();
// void show_status(const char* status_text);
// void update_display();
#endif // DISPLAY_MANAGER_H
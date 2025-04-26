#include "display_manager.h"
#include "../config/config.h"
#include <Arduino.h> // Include Arduino core for Serial

// Instantiate the display object for ILI9341 SPI display
// Parameters: CS, DC, RST pins (MOSI and SCK are usually hardware SPI)
Adafruit_ILI9341 display = Adafruit_ILI9341(TFT_CS, TFT_DC, TFT_RST);

/**
 * @brief Initializes the TFT display object and clears the screen.
 * @return true if initialization is successful (assumed for now), false otherwise.
 */
bool DisplayManager::setup_display() {
    // SPI communication is typically initialized by the library's begin() method.

    // Initialize the ILI9341 display
    display.begin();

    // Check if initialization was successful (optional, begin() might not return status)
    // Add specific checks here if the library provides them.
    // For now, assume success if no crash.

    // Initial display state
    display.fillScreen(ILI9341_BLACK); // Clear screen to black
    display.setTextSize(2);            // Set default text size (adjust as needed)
    display.setTextColor(ILI9341_WHITE); // Set default text color
    display.setTextWrap(true);         // Enable text wrapping
    display.setCursor(10, 10);         // Set initial cursor position (adjust as needed)

    // No display.display() needed for Adafruit_ILI9341, drawing is immediate

    Serial.println(F("ILI9341 TFT display initialized."));
    return true; // Assume success for now
}

/**
 * @brief Clears the entire display area by filling it with black.
 *        Resets the cursor position to a default top-left location.
 */
void DisplayManager::clear_display() {
    display.fillScreen(ILI9341_BLACK); // Fill screen with black
    display.setCursor(10, 10);         // Reset cursor to default position after clearing
}

/**
 * @brief Displays the faculty's current status (e.g., "Present", "Unavailable")
 *        in a designated area at the top of the screen. Clears the area first.
 * @param status_text The status string to display.
 */
void DisplayManager::show_status(const char* status_text) {
    // Define the rectangular area for the status text at the top
    int status_x = 0; // Start from left edge
    int status_y = 0; // Start from top edge
    int status_height = 25; // Estimated height for size 2 text + padding
    int status_width = SCREEN_WIDTH; // Use full width

    // Clear the status area first
    display.fillRect(status_x, status_y, status_width, status_height, ILI9341_BLACK);

    // Set text properties and draw the new status
    display.setTextSize(2);
    display.setTextColor(ILI9341_WHITE);
    display.setCursor(status_x + 10, status_y + 10); // Position cursor within the cleared area
    display.println(status_text); // Use println to handle line breaks if needed
}

/**
 * @brief Placeholder/Compatibility function. For ILI9341 with Adafruit_GFX,
 *        drawing commands often update the display directly. This is not needed.
 */
void DisplayManager::update_display() {
    // This function is intentionally left empty for Adafruit_ILI9341.
    // Leaving the function definition empty for now to avoid breaking calls,
    // but calls to it should be removed from the .ino file.
}

// --- Function-based approach section removed as class approach is used ---
/**
 * @brief Displays details of an incoming consultation request
 *        (Student ID, Request Text) in the area below the status bar.
 *        Clears the request area before drawing.
 * @param student_id The ID of the student making the request.
 * @param request_text The text of the consultation request.
 */
void DisplayManager::show_request(const char* student_id, const char* request_text) {
    if (student_id == nullptr || request_text == nullptr) {
        Serial.println(F("Error: Null pointer passed to show_request."));
        return; // Don't attempt to display null data
    }

    // --- Clear the request area (optional, simple approach clears below status) ---
    // Get current status text height (assuming size 2, approx 16 pixels high + padding)
    int status_height = 25; // Estimate based on size 2 text + padding
    // Clear the area below the status
    display.fillRect(0, status_height, SCREEN_WIDTH, SCREEN_HEIGHT - status_height, ILI9341_BLACK);

    // --- Display the new request ---
    display.setTextSize(1); // Use smaller text for request details
    display.setTextColor(ILI9341_WHITE);
    display.setCursor(0, status_height + 5); // Position cursor below status area with some padding

    display.print(F("From: "));
    display.println(student_id);

    // Print request text, potentially wrapping
    display.setCursor(0, display.getCursorY() + 2); // Move down slightly for the message
    display.println(request_text); // println should handle wrapping if enabled

    // Note: No display.display() needed for ILI9341
    Serial.println(F("Displayed new request on TFT."));
}
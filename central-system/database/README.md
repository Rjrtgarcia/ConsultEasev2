# Central System - Database Module

This module handles communication with the backend database, primarily Firebase Firestore.

## `firebase_client.py`

Provides the `FirebaseClient` class, which encapsulates methods for:
*   Initializing connection to Firebase using service account credentials.
*   Performing CRUD (Create, Read, Update, Delete) operations on the `faculty` collection.
*   Logging consultation requests to the `requests` collection.
*   Fetching faculty data.
*   Includes basic offline caching and synchronization logic (though potentially legacy or incomplete for all operations).

See the main project `README.md` for Firebase setup instructions.
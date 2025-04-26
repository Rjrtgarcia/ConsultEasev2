#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ConsultEase Central System
Firebase Database Client
"""

import os
import json
import logging
import threading
import time
from pathlib import Path
from datetime import datetime, timedelta

# Firebase imports
try:
    import firebase_admin
    from firebase_admin import credentials, firestore, db as realtime_db
    import pyrebase
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False

logger = logging.getLogger(__name__)

class FirebaseClient:
    """Firebase database client for ConsultEase"""
    
    def __init__(self, service_account_path=None, config_path=None):
        """
        Initialize Firebase client with service account credentials.
        Sets up Firestore client and handles offline mode initialization if connection fails.
        """
        self.db = None # Firestore client instance
        self.rtdb = None # Realtime Database reference (optional)
        self.firebase_app = None
        self.auth = None # Pyrebase auth instance (currently unused)
        self.storage = None # Pyrebase storage instance (currently unused)
        self.offline_mode = False # Flag indicating if the client is operating offline
        self.offline_cache = {} # In-memory cache for data when offline
        self.offline_cache_file = Path("offline_cache.json") # File to persist offline cache
        
        # Try to initialize Firebase
        if FIREBASE_AVAILABLE:
            try:
                self._init_firebase(service_account_path, config_path)
            except Exception as e:
                logger.error(f"Firebase initialization failed: {e}")
                self.offline_mode = True
        else:
            logger.warning("Firebase libraries not available, using offline mode")
            self.offline_mode = True
        
        # Load offline cache if in offline mode
        if self.offline_mode:
            self._load_offline_cache()
            
        # Start a background thread to periodically attempt reconnection and sync if starting in offline mode.
        if self.offline_mode:
            self.sync_thread = threading.Thread(target=self._sync_thread, daemon=True)
            self.sync_thread.start()
            logger.info("Offline mode active. Sync thread started.")
    
    def _init_firebase(self, service_account_path=None, config_path=None):
        """Initialize Firebase with the provided credentials"""
        # Find service account file
        if not service_account_path:
            service_account_path = self._find_service_account()
        
        if not service_account_path:
            raise FileNotFoundError("Firebase service account file not found")
        
        # Initialize Firebase Admin SDK only if it hasn't been initialized
        if not firebase_admin._apps:
            cred = credentials.Certificate(service_account_path)
            try:
                # Keep databaseURL for potential RTDB use elsewhere, though not strictly needed for Firestore
                self.firebase_app = firebase_admin.initialize_app(cred, {
                    'databaseURL': 'https://consultease-prod.firebaseio.com'
                })
                logger.info("Firebase Admin SDK initialized successfully.")
            except Exception as e:
                logger.error(f"Firebase Admin SDK initialization failed: {e}")
                raise  # Re-raise the exception to be caught by the caller
        else:
            # Get the default app if already initialized
            self.firebase_app = firebase_admin.get_app()
            logger.info("Firebase Admin SDK already initialized.")

        # Initialize Firestore
        try:
            self.db = firestore.client(app=self.firebase_app)
            # Define collection references
            self.faculty_collection = self.db.collection('faculty')
            self.requests_collection = self.db.collection('requests') # Add requests collection
            self.auth_logs_collection = self.db.collection('auth_logs') # Add auth logs collection for consistency
            self.students_collection = self.db.collection('students') # Add students collection
            logger.info("Firestore client initialized.")
        except Exception as e:
            logger.error(f"Firestore client initialization failed: {e}")
            raise # Re-raise

        # Initialize Realtime Database (keep for potential other uses)
        try:
            self.rtdb = realtime_db.reference(app=self.firebase_app)
            logger.info("Realtime Database reference obtained.")
        except Exception as e:
            # Log RTDB init failure but don't necessarily raise if Firestore is primary
            logger.warning(f"Realtime Database reference initialization failed: {e}")
            self.rtdb = None

        # Pyrebase initialization removed as per task scope

        logger.info("Firebase components initialized.")
    
    def _find_service_account(self):
        """Find the Firebase service account file"""
        # Common locations to check
        locations = [
            "serviceAccountKey.json",
            "service-account.json",
            "firebase-service-account.json",
            "config/serviceAccountKey.json",
            "../config/serviceAccountKey.json",
            os.path.expanduser("~/.config/consultease/serviceAccountKey.json")
        ]
        
        for location in locations:
            if os.path.exists(location):
                return location
        
        return None
    
    def _load_offline_cache(self):
        """Loads the offline data cache from the JSON file if it exists."""
        if self.offline_cache_file.exists():
            logger.info(f"Loading offline cache from {self.offline_cache_file}...")
            try:
                with open(self.offline_cache_file, 'r') as f:
                    self.offline_cache = json.load(f)
                logger.info("Offline cache loaded")
            except Exception as e:
                logger.error(f"Error loading offline cache: {e}")
                self.offline_cache = {}
    
    def _save_offline_cache(self):
        """Saves the current in-memory offline cache to the JSON file."""
        logger.debug(f"Saving offline cache to {self.offline_cache_file}...")
        try:
            with open(self.offline_cache_file, 'w') as f:
                json.dump(self.offline_cache, f)
            logger.debug("Offline cache saved")
        except Exception as e:
            logger.error(f"Error saving offline cache: {e}")
    
    def _sync_thread(self):
        """Background thread to attempt Firebase sync when in offline mode"""
        while True:
            time.sleep(30)  # Try to sync every 30 seconds
            
            if not self.offline_mode:
                continue
                
            try:
                # Try to initialize Firebase again
                self._init_firebase()
                
                # If successful, we're back online
                self.offline_mode = False
                
                # Sync offline changes
                self._sync_offline_changes()
                
                logger.info("Reconnected to Firebase and synced offline changes")
            except Exception as e:
                logger.debug(f"Still in offline mode: {e}")
    
    def _sync_offline_changes(self):
        """
        Attempts to synchronize changes stored in the offline cache with the live Firebase database.
        Processes create, update, and delete operations marked in the cache.
        """
        if not self.offline_cache:
            logger.info("Offline cache is empty, nothing to sync.")
            return
            
        # Define collections to sync (add 'requests' and 'auth_logs')
        collections_to_sync = ['users', 'consultation_requests', 'auth_logs', 'requests']

        for collection in collections_to_sync:
            if collection not in self.offline_cache:
                continue
            items = self.offline_cache[collection]
            logger.info(f"Syncing {len(items)} items from offline cache for collection: {collection}")
            for doc_id, data in items.items():
                if not isinstance(data, dict): # Skip non-dict items if any corruption occurred
                    logger.warning(f"Skipping invalid item in offline cache: {collection}/{doc_id}")
                    continue
                try:
                    # Check the '_operation' metadata field to determine action
                    operation = data.get('_operation')
                    if operation == 'delete':
                        # Perform a delete operation in Firestore
                        target_collection = self.db.collection(collection)
                        target_collection.document(doc_id).delete()
                        logger.info(f"Synced offline delete for {collection}/{doc_id}")
                    elif operation == 'create' or operation == 'update':
                        # Perform a set/update operation in Firestore
                        # Remove internal metadata fields (like '_operation', '_updated_at') before writing
                        clean_data = {k: v for k, v in data.items() if not k.startswith('_')}
                        target_collection = self.db.collection(collection)
                        # Use set with merge=True to handle both creates and updates gracefully
                        target_collection.document(doc_id).set(clean_data, merge=True)
                        logger.info(f"Synced offline {operation} for {collection}/{doc_id}")
                    else:
                        logger.warning(f"Unknown operation '{data.get('_operation')}' for {collection}/{doc_id}")

                except Exception as e:
                    logger.error(f"Error syncing document {collection}/{doc_id}: {e}")
                    # Decide if we should keep the item in cache or discard? For now, keep.

        # Clear synced collections from the cache after attempting sync
        for collection in collections_to_sync:
            if collection in self.offline_cache:
                # Ideally, only remove successfully synced items, but for simplicity now, clear all attempted.
                # A more robust implementation would track individual item sync status.
                del self.offline_cache[collection]

        self._save_offline_cache()
        self._save_offline_cache() # Save cache after clearing synced items

# --- Potentially Legacy Methods (Using 'users' collection structure) ---
# These methods seem based on an older structure where faculty were part of a general 'users' collection.
# The newer CRUD methods (add_faculty, get_faculty, etc.) target the dedicated 'faculty' collection.
# Keep these for now, but mark as potentially legacy.

def get_user_by_rfid(self, rfid_tag):
    """
    [Legacy?] Get user data by RFID tag from the 'users' collection.
    Includes offline cache check.
    """
    if self.offline_mode:
        # Check offline cache for 'users' collection
            users = self.offline_cache.get('users', {})
            for user_id, user_data in users.items():
                if user_data.get('rfid_tag') == rfid_tag:
                    return {**user_data, 'id': user_id}
            return None
        
        # If not offline, attempt to query Firestore
    else: # Correctly aligned with 'if self.offline_mode:'
        try: # Indented under 'else:'
            # Query Firestore for the user with this RFID tag
            logger.debug(f"Querying Firestore for RFID {rfid_tag}")
            users_ref = self.db.collection('users')
            query = users_ref.where('rfid_tag', '==', rfid_tag).limit(1)
            results = query.get()

            for doc in results:
                user_data = doc.to_dict()
                logger.debug(f"Found user {doc.id} in Firestore for RFID {rfid_tag}")
                return {**user_data, 'id': doc.id}

            logger.debug(f"RFID {rfid_tag} not found in Firestore.")
            return None # User not found
        except Exception as e: # Aligned with 'try:'
            logger.error(f"Error getting user by RFID from Firestore: {e}")

            # Switch to offline mode on error
            logger.warning("Switching to offline mode due to Firestore error.")
            self.offline_mode = True
            # Immediately retry using the offline cache logic
            logger.debug(f"Retrying get_user_by_rfid for {rfid_tag} in offline mode.")
            return self.get_user_by_rfid(rfid_tag)

    def get_faculty_list(self):
        """
        [Legacy?] Get list of all users marked with the 'faculty' role from the 'users' collection.
        Includes offline cache check and update.
        """
        if self.offline_mode:
            # Return from offline cache ('users' collection)
            faculty_list = []
            users = self.offline_cache.get('users', {})
            for user_id, user_data in users.items():
                if 'faculty' in user_data.get('roles', []):
                    faculty_list.append({**user_data, 'id': user_id})
            return faculty_list
        
        try:
            # Query Firestore for all faculty members
            users_ref = self.db.collection('users')
            query = users_ref.where('roles', 'array_contains', 'faculty')
            results = query.get()
            
            faculty_list = []
            for doc in results:
                user_data = doc.to_dict()
                faculty_list.append({**user_data, 'id': doc.id})
            
            # Cache the results
            if 'users' not in self.offline_cache:
                self.offline_cache['users'] = {}
            
            for faculty in faculty_list:
                faculty_id = faculty.pop('id')
                self.offline_cache['users'][faculty_id] = faculty
                faculty['id'] = faculty_id  # Put it back for the return value
            
            self._save_offline_cache()
            
            return faculty_list
        except Exception as e:
            logger.error(f"Error getting faculty list: {e}")
            
            # Switch to offline mode on error
            self.offline_mode = True
            return self.get_faculty_list() # Retry in offline mode

    def update_faculty_status(self, faculty_id, status):
        """
        [Legacy?] Update faculty status in both Firestore 'users' collection and Realtime Database.
        Includes offline cache update.
        """
        if self.offline_mode:
            # Update in offline cache ('users' collection)
            if 'users' not in self.offline_cache:
                self.offline_cache['users'] = {}
            
            if faculty_id in self.offline_cache['users']:
                self.offline_cache['users'][faculty_id]['status'] = status
                self.offline_cache['users'][faculty_id]['_updated_at'] = datetime.now().isoformat()
            else:
                self.offline_cache['users'][faculty_id] = {
                    'status': status,
                    '_updated_at': datetime.now().isoformat(),
                    '_operation': 'update'
                }
            
            self._save_offline_cache()
            return True
        
        try:
            # Update in Firestore
            user_ref = self.db.collection('users').document(faculty_id)
            user_ref.update({
                'status': status,
                'updated_at': firestore.SERVER_TIMESTAMP
            })
            
            # Also update in Realtime Database for MQTT triggers
            self.rtdb.reference(f'faculty/{faculty_id}/status').set(status)
            
            return True
        except Exception as e:
            logger.error(f"Error updating faculty status: {e}")
            
            # Switch to offline mode on error
            self.offline_mode = True
            return self.update_faculty_status(faculty_id, status) # Retry in offline mode

    def log_auth_event(self, user_id, success, details=None):
        """
        Log authentication event to the 'auth_logs' collection.
        Includes offline cache logging.
        """
        if self.offline_mode:
            # Log in offline cache ('auth_logs' collection)
            if 'auth_logs' not in self.offline_cache:
                self.offline_cache['auth_logs'] = {}
            
            log_id = f"log_{int(time.time())}"
            self.offline_cache['auth_logs'][log_id] = {
                'user_id': user_id,
                'success': success,
                'details': details,
                'timestamp': datetime.now().isoformat(),
                '_operation': 'create'
            }
            
            self._save_offline_cache()
            return True
        
        try:
            # Log in Firestore using the collection reference
            # log_ref = self.db.collection('auth_logs').document() # Old way
            log_ref = self.auth_logs_collection.document() # Use defined collection ref
            log_ref.set({
                'user_id': user_id,
                'success': success,
                'details': details,
                'timestamp': firestore.SERVER_TIMESTAMP
            })
            
            return True
        except Exception as e:
            logger.error(f"Error logging auth event: {e}")
            
            # Switch to offline mode on error
            self.offline_mode = True
            return self.log_auth_event(user_id, success, details) # Retry in offline mode

    def create_consultation_request(self, student_id, faculty_id, topic):
        """
        [Legacy?] Create a new consultation request in both Firestore 'consultation_requests'
        collection and Realtime Database.
        Includes offline cache creation.
        """
        if self.offline_mode:
            # Create in offline cache ('consultation_requests' collection)
            if 'consultation_requests' not in self.offline_cache:
                self.offline_cache['consultation_requests'] = {}
            
            request_id = f"req_{int(time.time())}"
            self.offline_cache['consultation_requests'][request_id] = {
                'student_id': student_id,
                'faculty_id': faculty_id,
                'topic': topic,
                'status': 'pending',
                'created_at': datetime.now().isoformat(),
                '_operation': 'create'
            }
            
            self._save_offline_cache()
            return request_id
        
        try:
            # Create in Firestore
            request_ref = self.db.collection('consultation_requests').document()
            request_ref.set({
                'student_id': student_id,
                'faculty_id': faculty_id,
                'topic': topic,
                'status': 'pending',
                'created_at': firestore.SERVER_TIMESTAMP
            })
            
            # Also create in Realtime Database for MQTT triggers
            self.rtdb.reference(f'faculty/{faculty_id}/requests/{request_ref.id}').set({
                'student_id': student_id,
                'topic': topic,
                'status': 'pending',
                'timestamp': int(time.time() * 1000)
            })
            
            return request_ref.id
        except Exception as e:
            logger.error(f"Error creating consultation request: {e}")
            
            # Switch to offline mode on error
            self.offline_mode = True
            return self.create_consultation_request(student_id, faculty_id, topic) # Retry in offline mode

    def is_offline(self):
        """Returns True if the Firebase client is currently operating in offline mode, False otherwise."""
        return self.offline_mode

    def log_request(self, request_data):
        """
        Logs a consultation request to the 'requests' collection in Firestore.

       Args:
           request_data (dict): A dictionary containing request details
                                (e.g., student_id, request_text, timestamp, status).

       Returns:
           str | None: The document ID if successful (or temporary offline ID), None otherwise.
       """
        if self.offline_mode:
            logger.info("Offline mode: Logging request to offline cache.")
            if 'requests' not in self.offline_cache:
               self.offline_cache['requests'] = {}

            # Ensure timestamp is included if not provided
            if 'timestamp' not in request_data:
                request_data['timestamp'] = datetime.now().isoformat()

            # Generate a temporary ID for offline storage
            offline_id = f"offline_req_{int(time.time() * 1000)}"
            self.offline_cache['requests'][offline_id] = {
               **request_data,
               '_operation': 'create' # Mark as a creation operation for sync
           }
            self._save_offline_cache()
            return offline_id # Return the temporary ID

        try:
            # Add the request data to the 'requests' collection
            # Firestore will auto-generate an ID
           update_time, doc_ref = self.requests_collection.add(request_data)
           logger.info(f"Consultation request logged successfully with ID: {doc_ref.id}")
           return doc_ref.id
        except Exception as e:
            logger.error(f"Error logging consultation request: {e}")
            # Switch to offline mode on error? Maybe too aggressive here.
           # Consider just returning None or raising the exception.
           # For now, just log and return None.
           # self.offline_mode = True # Optional: switch to offline on failure
           # return self.log_request(request_data) # Optional: retry in offline mode
            return None

    # --- Faculty CRUD Operations ---

    def add_faculty(self, faculty_id, faculty_data):
        """
        Adds a new faculty document to the 'faculty' collection.

        Args:
            faculty_id (str | None): The specific ID for the new faculty document.
                                     If None, Firestore will auto-generate an ID.
            faculty_data (dict): A dictionary containing the faculty member's data.

        Returns:
            str | None: The document ID if successful, None otherwise.
        """
        if self.offline_mode:
            logger.warning("Offline mode: Cannot add faculty.")
            # TODO: Implement offline caching for add_faculty if needed
            return None
        
        try:
            if faculty_id:
                doc_ref = self.faculty_collection.document(faculty_id)
                doc_ref.set(faculty_data)
                logger.info(f"Faculty added successfully with ID: {faculty_id}")
                return faculty_id
            else:
                # Let Firestore auto-generate the ID
                doc_ref = self.faculty_collection.add(faculty_data)
                logger.info(f"Faculty added successfully with auto-generated ID: {doc_ref[1].id}")
                # The add() method returns a tuple (timestamp, DocumentReference)
                return doc_ref[1].id
        except Exception as e:
            logger.error(f"Error adding faculty (ID: {faculty_id}): {e}")
            return None

    def get_faculty(self, faculty_id):
        """
        Retrieves a specific faculty document by its ID from the 'faculty' collection.

        Args:
            faculty_id (str): The ID of the faculty document to retrieve.

        Returns:
            dict | None: The faculty data dictionary if found, None otherwise.
        """
        if self.offline_mode:
            logger.warning("Offline mode: Cannot get faculty.")
            # TODO: Implement offline caching for get_faculty if needed
            return None

        if not faculty_id:
            logger.error("Error getting faculty: faculty_id cannot be empty.")
            return None

        try:
            doc_ref = self.faculty_collection.document(faculty_id)
            doc_snapshot = doc_ref.get()
            if doc_snapshot.exists:
                logger.info(f"Faculty retrieved successfully: {faculty_id}")
                return doc_snapshot.to_dict()
            else:
                logger.warning(f"Faculty not found: {faculty_id}")
                return None
        except Exception as e:
            logger.error(f"Error getting faculty (ID: {faculty_id}): {e}")
            return None

    def get_all_faculty(self):
        """
        Retrieves all documents from the 'faculty' collection.

        Returns:
            list[dict] | None: A list of faculty data dictionaries, or None on error.
                                Returns an empty list if the collection is empty.
        """
        if self.offline_mode:
            logger.warning("Offline mode: Cannot get all faculty.")
            # TODO: Implement offline caching for get_all_faculty if needed
            return None
            
        try:
            faculty_list = []
            docs = self.faculty_collection.stream() # Use stream() for potentially large collections
            for doc in docs:
                faculty_data = doc.to_dict()
                faculty_data['id'] = doc.id # Optionally include the document ID
                faculty_list.append(faculty_data)
            logger.info(f"Retrieved {len(faculty_list)} faculty members.")
            return faculty_list
        except Exception as e:
            logger.error(f"Error getting all faculty: {e}")
            return None

    def update_faculty(self, faculty_id, update_data):
        """
        Updates specific fields in a faculty document in the 'faculty' collection.

        Args:
            faculty_id (str): The ID of the faculty document to update.
            update_data (dict): A dictionary containing the fields and new values to update.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        if self.offline_mode:
            logger.warning("Offline mode: Cannot update faculty.")
            # TODO: Implement offline caching for update_faculty if needed
            return False

        if not faculty_id:
            logger.error("Error updating faculty: faculty_id cannot be empty.")
            return False
        if not update_data:
            logger.warning("No update data provided for faculty: {faculty_id}")
            return True # No changes needed, consider it successful

        try:
            doc_ref = self.faculty_collection.document(faculty_id)
            # Use update() to modify specific fields without overwriting the entire document
            doc_ref.update(update_data)
            logger.info(f"Faculty updated successfully: {faculty_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating faculty (ID: {faculty_id}): {e}")
            return False

    def delete_faculty(self, faculty_id):
        """
        Deletes a faculty document by its ID from the 'faculty' collection.

        Args:
            faculty_id (str): The ID of the faculty document to delete.

        Returns:
            bool: True if the deletion was successful, False otherwise.
        """
        if self.offline_mode:
            logger.warning("Offline mode: Cannot delete faculty.")
            # TODO: Implement offline caching for delete_faculty if needed
            return False

        if not faculty_id:
            logger.error("Error deleting faculty: faculty_id cannot be empty.")
            return False
            
        try:
            doc_ref = self.faculty_collection.document(faculty_id)
            doc_ref.delete()
            logger.info(f"Faculty deleted successfully: {faculty_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting faculty (ID: {faculty_id}): {e}")
            return False
# --- Student CRUD Operations ---

    def add_student(self, student_data):
        """
        Adds a new student document to the 'students' collection.

        Args:
            student_data (dict): A dictionary containing student details
                                 (e.g., student_id, name, rfid_tag).

        Returns:
            str | None: The Firestore document ID if successful, None otherwise.
        """
        if self.offline_mode:
            logger.warning("Offline mode: Cannot add student directly. Operation will be queued if sync mechanism supports it.")
            # Basic offline queuing could be added here if needed, similar to log_request
            return None # Or a temporary offline ID if implementing offline queuing

        if not self.students_collection:
            logger.error("Students collection reference not initialized.")
            return None

        try:
            # Add timestamp if not present
            if 'created_at' not in student_data:
                student_data['created_at'] = firestore.SERVER_TIMESTAMP
            if 'updated_at' not in student_data:
                 student_data['updated_at'] = firestore.SERVER_TIMESTAMP

            update_time, doc_ref = self.students_collection.add(student_data)
            logger.info(f"Student added successfully with ID: {doc_ref.id}")
            return doc_ref.id
        except Exception as e:
            logger.error(f"Error adding student: {e}")
            # Consider switching to offline mode here if appropriate
            # self.offline_mode = True
            return None

    def get_student(self, doc_id):
        """
        Retrieves a student document by its Firestore document ID.

        Args:
            doc_id (str): The Firestore document ID of the student.

        Returns:
            dict | None: The student data dictionary if found, None otherwise.
        """
        if self.offline_mode:
            logger.warning("Offline mode: Cannot get student directly. Check offline cache if implemented.")
            # Offline cache retrieval logic could be added here
            return None

        if not self.students_collection:
            logger.error("Students collection reference not initialized.")
            return None

        try:
            doc_ref = self.students_collection.document(doc_id)
            doc = doc_ref.get()
            if doc.exists:
                student_data = doc.to_dict()
                student_data['id'] = doc.id # Include Firestore doc ID
                logger.debug(f"Student {doc_id} retrieved successfully.")
                return student_data
            else:
                logger.warning(f"Student document with ID {doc_id} not found.")
                return None
        except Exception as e:
            logger.error(f"Error getting student {doc_id}: {e}")
            # Consider switching to offline mode
            # self.offline_mode = True
            return None

    def get_student_by_rfid(self, rfid_tag):
        """
        Retrieves a student document by their RFID tag.

        Args:
            rfid_tag (str): The RFID tag associated with the student.

        Returns:
            dict | None: The student data dictionary (including Firestore doc ID)
                         if found, None otherwise. Returns the first match.
        """
        if self.offline_mode:
            logger.warning("Offline mode: Cannot query students by RFID. Check offline cache if implemented.")
            # Offline cache query logic could be added here
            return None

        if not self.students_collection:
            logger.error("Students collection reference not initialized.")
            return None

        try:
            query = self.students_collection.where('rfid_tag', '==', rfid_tag).limit(1)
            results = query.stream() # Use stream() for potentially large result sets (though limit(1) makes it small)

            for doc in results:
                student_data = doc.to_dict()
                student_data['id'] = doc.id # Include Firestore doc ID
                logger.info(f"Found student {doc.id} for RFID tag {rfid_tag}")
                return student_data

            logger.info(f"No student found with RFID tag {rfid_tag}")
            return None
        except Exception as e:
            logger.error(f"Error querying student by RFID tag {rfid_tag}: {e}")
            # Consider switching to offline mode
            # self.offline_mode = True
            return None

    def get_all_students(self):
        """
        Retrieves all documents from the 'students' collection.

        Returns:
            list[dict]: A list of student data dictionaries (including Firestore doc IDs),
                        or an empty list if none found or in case of error.
        """
        if self.offline_mode:
            logger.warning("Offline mode: Cannot get all students. Check offline cache if implemented.")
            # Offline cache retrieval logic could be added here
            return []

        if not self.students_collection:
            logger.error("Students collection reference not initialized.")
            return []

        students_list = []
        try:
            docs = self.students_collection.stream()
            for doc in docs:
                student_data = doc.to_dict()
                student_data['id'] = doc.id # Include Firestore doc ID
                students_list.append(student_data)
            logger.info(f"Retrieved {len(students_list)} students.")
            return students_list
        except Exception as e:
            logger.error(f"Error getting all students: {e}")
            # Consider switching to offline mode
            # self.offline_mode = True
            return [] # Return empty list on error

    def update_student(self, doc_id, update_data):
        """
        Updates specific fields in a student document.

        Args:
            doc_id (str): The Firestore document ID of the student to update.
            update_data (dict): A dictionary containing the fields to update.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        if self.offline_mode:
            logger.warning("Offline mode: Cannot update student directly. Operation will be queued if sync mechanism supports it.")
            # Offline queuing logic could be added here
            return False

        if not self.students_collection:
            logger.error("Students collection reference not initialized.")
            return False

        try:
            # Add update timestamp
            if 'updated_at' not in update_data:
                update_data['updated_at'] = firestore.SERVER_TIMESTAMP

            doc_ref = self.students_collection.document(doc_id)
            doc_ref.update(update_data)
            logger.info(f"Student {doc_id} updated successfully.")
            return True
        except Exception as e:
            logger.error(f"Error updating student {doc_id}: {e}")
            # Consider switching to offline mode
            # self.offline_mode = True
            return False

    def delete_student(self, doc_id):
        """
        Deletes a student document by its Firestore document ID.

        Args:
            doc_id (str): The Firestore document ID of the student to delete.

        Returns:
            bool: True if the deletion was successful, False otherwise.
        """
        if self.offline_mode:
            logger.warning("Offline mode: Cannot delete student directly. Operation will be queued if sync mechanism supports it.")
            # Offline queuing logic could be added here
            return False

        if not self.students_collection:
            logger.error("Students collection reference not initialized.")
            return False

        try:
            doc_ref = self.students_collection.document(doc_id)
            doc_ref.delete()
            logger.info(f"Student {doc_id} deleted successfully.")
            return True
        except Exception as e:
            logger.error(f"Error deleting student {doc_id}: {e}")
            # Consider switching to offline mode
            # self.offline_mode = True
            return False
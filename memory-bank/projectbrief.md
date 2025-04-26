# ConsultEase Project Brief
*Last updated: {{DATE}}*  

## Project Overview
Objective: Develop integrated student-faculty interaction system with dual hardware components  
Scope: Raspberry Pi Central System + ESP32 Faculty Units  
Key Milestones: RFID auth, real-time status, MQTT comms, admin interface  

## Core Requirements
1. Dual hardware integration (RPi + ESP32)
2. Role-based access control (RBAC)
3. Cross-device status sync (</=500ms latency)
4. Touch-optimized PyQt interface (</=2s response)
5. BLE presence detection (</=10m range)

## System Boundaries
- Includes: Firebase Realtime DB integration, RFID auth, offline cache
- Excludes: Local SQL databases, mobile app integration

// File version: 1.0-init

# Specification: MVP - Basic License Server

## Overview

A minimal self-hosted license management server that enables tool creators to protect their software with one-time purchase licenses limited to a single device.

## Goals

- Generate and manage license keys
- Validate licenses against device fingerprints
- Limit each license to one device
- Provide admin dashboard for license management

## User Stories

### Tool Creator (Admin)
- **US-001:** As an admin, I can generate new license keys so customers can activate my tool
- **US-002:** As an admin, I can view all licenses and their activation status
- **US-003:** As an admin, I can see which device is using each license
- **US-004:** As an admin, I can revoke/deactivate a license remotely

### End User (Customer)
- **US-005:** As a user, I can activate my license key on my device
- **US-006:** As a user, I receive a clear message if activation fails (invalid key, already used)
- **US-007:** As a user, I can deactivate my device to move license to another device

## Functional Requirements

### License Management
- **FR-001:** System generates license keys in format `XXXX-XXXX-XXXX-XXXX` (alphanumeric)
- **FR-002:** Each license allows activation on exactly 1 device
- **FR-003:** License keys are unique and cryptographically random
- **FR-004:** Licenses are one-time purchase (no expiration in MVP)

### Device Fingerprinting
- **FR-005:** Collect hardware fingerprint (CPU ID, disk serial, motherboard ID)
- **FR-006:** Collect MAC address as secondary identifier
- **FR-007:** Generate unique device ID from combined fingerprint
- **FR-008:** Store device fingerprint securely on activation

### Activation Flow
- **FR-009:** Validate license key exists and is not already activated
- **FR-010:** If device limit reached, block activation with user-friendly message
- **FR-011:** On successful activation, link device ID to license
- **FR-012:** Return activation status to client

### Admin Dashboard
- **FR-013:** Display list of all licenses with status (active/inactive)
- **FR-014:** Show device details for activated licenses
- **FR-015:** Provide ability to generate new license keys
- **FR-016:** Provide ability to revoke/deactivate licenses

## Non-Functional Requirements

- **NFR-001:** API response time < 500ms
- **NFR-002:** Support 1000 concurrent license validations
- **NFR-003:** All API endpoints authenticated with JWT
- **NFR-004:** Device fingerprints stored hashed (not plaintext)

## Out of Scope (MVP)

- Subscription/recurring billing
- Time-based expiration
- Multiple device limits (>1)
- Email notifications
- Usage analytics
- Multi-language UI (English only for MVP)

# RaahiKart
```mermaid
graph TD
    subgraph "Phase 1 - Onboarding and Verification"
        A[User Downloads App] --> B[Enter Phone and Verify with OTP]
        B --> C[Mandatory KYC - Upload Govt ID and Live Selfie Check]
        C --> D{RaahiKart Admin Verifies KYC}
        D -- Approved --> E[Verified User - Profile Activated]
        D -- Rejected --> F[Notification to Re-submit KYC]
        F --> C
    end

    E --> G{Choose Your Role}
    G -- SEND (P2P) --> H[Set up Payment Method - UPI or Wallet]
    G -- RIDE --> I[Set up Payout Account and Go Live]
    G -- Register Business --> J_BUS[Business Verification - GSTIN or License and Bank Details]
    J_BUS --> K_BUS[Business Dashboard Activated]

    subgraph "Phase 2A - Peer to Peer Delivery"
        H --> J[Sender Creates Task - Pickup and Drop Info, Item Details, Confirm Fee]
        J --> K[Backend Matches Best Rider for Task]
        I --> K
        K --> L[Rider Accepts P2P Task]
        L --> M[Match Confirmed - Chat Enabled and Tracking Starts]
        M --> N[P2P Pickup - Sender Gives OTP]
        N --> Q[Delivery In Progress]
        Q --> R[P2P Delivery - Recipient Gives OTP]
        R --> T{P2P Delivery Complete}
        T -- Yes --> V[Payment Sent to Rider, Commission Deducted]
        V --> W[Mutual Rating]
        W --> X[End of Flow]
    end

    subgraph "Phase 2B - Business to Consumer Delivery"
        H --> B1[Customer Places Order - Browse Shops and Add to Cart]
        K_BUS --> B1
        B1 --> B2[Customer Pays Total in Escrow - Item plus Delivery Fee]
        B2 --> B3[Shop Notified - Prepares Package]
        B2 --> B4[Backend Matches Best Rider for B2C]
        I --> B4
        B4 --> B5[Rider Accepts B2C Task - Sees Only Delivery Fee]
        B5 --> B6[Rider Picks Up from Shop and Gives OTP]
        B3 --> B6
        B6 --> B7[Delivery In Progress - Customer Tracks Live]
        B7 --> B8[Delivery - Customer Gives OTP]
        B8 --> B9{B2C Delivery Complete}
        B9 -- Yes --> B10[Escrow Settlement - Item Cost to Shop, Fee to Rider, Platform Keeps Share]
        B10 --> B11[All Parties Rate Each Other]
        B11 --> X
    end

    subgraph "Exception Handling"
        Z00[ ]:::invisible
        style Z00 fill:#ffffff,stroke:#ffffff
        M -- Issue Reported --> Z[Report Issue]
        B7 -- Issue Reported --> Z
        Z --> ZA[Dispute Started - Payment on Hold]
        ZA --> ZB[Support Agent Investigates]
        ZB --> ZC{Agent Decision}
        ZC --> X
    end

```
# 📅 Project Timeline

This timeline outlines our development plan over three weeks, culminating in a final deployed application and presentation.

---

## 🟩 Week 1 (Goal: Core Functionality & Onboarding)

- 🔧 **Backend**
  - Project Setup
  - Database Schema Design

- 🎨 **Frontend**
  - User Onboarding UI
  - KYC Flow Implementation

- 🔗 **Integration**
  - Connect Onboarding Flow to Backend

- ✏️ **Frontend**
  - Profile Page UI
  - Task Creation UI

---

## 🟨 Week 2 (Goal: 80% Completion – End-to-End Flow)

- 🧠 **Backend**
  - Smart Matching Logic
  - Peer-to-Peer (P2P) Interaction Logic

- 📱 **Frontend**
  - Live P2P Tracking UI
  - OTP Verification UI

- 🔄 **Integration**
  - Full End-to-End P2P Flow Test

- 🧾 **Parallel Task**
  - Business Onboarding Panel/UI

- ✅ **Milestone**
  - 80% Completion Achieved

---

## 🟥 Week 3 (Goal: Finalize, Deploy & Document)

- 👥 **Feature Development**
  - B2C Flow (UI + Backend)

- 🧼 **Quality**
  - UI Polishing
  - Bug Fixing

- 🧪 **Testing**
  - Final End-to-End Test Cycle

- 🚀 **Deployment**
  - Live Server Deployment

- 📝 **Documentation**
  - Final Report Preparation
  - Presentation Slide Deck

- 🎯 **Milestone**
  - Final Project Submission & Demo

---

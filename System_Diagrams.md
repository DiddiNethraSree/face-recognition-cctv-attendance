# Proposed System Diagrams

You can copy the **Mermaid** code below into any Mermaid editor (like [Mermaid Live Editor](https://mermaid.live/)) to generate high-quality images for your PPT.

## 1. Proposed System Flow Chart
This flowchart demonstrates the end-to-end data flow from the camera feed to the user dashboards.

```mermaid
graph TD
    %% Hardware / Input Layer
    A[Start: CCTV / Webcam Feed] -->|Capture Frames| B(Face Detection Module)
    
    %% Processing Layer (Computer Vision)
    subgraph "Computer Vision Processing (OpenCV)"
    B --> C{Face Detected?}
    C -- Yes --> D[Feature Extraction]
    C -- No --> A
    D --> E[Compare with Trained Encodings]
    end

    %% Logic Layer
    subgraph "Backend Logic (Flask)"
    E --> F{Match Found?}
    F -- Yes --> G[Identify Student ID]
    F -- No --> A
    G --> H[Update Attendance in Database]
    end

    %% Data Layer
    subgraph "Database (SQLite)"
    H -->|Insert/Update| I[(Attendance Table)]
    J[(Users Table)] -.->|Validate Login| K
    end

    %% Presentation Layer (Web App)
    subgraph "Web Interface (Frontend)"
    L[User Login] -->|Request| K{Authenticate}
    K -- Success --> M[Role-Based Dashboard]
    I -->|Fetch Data| M
    
    M --> N[HOD View: Analytics]
    M --> O[Staff View: List]
    M --> P[Student View: Personal Log]
    end
```

---

## 2. Entity-Relationship (ER) Diagram
This diagram illustrates the database structure designed to maintain data integrity.

```mermaid
erDiagram
    %% Entities
    USERS {
        string user_id PK "Unique ID (e.g., student1)"
        string password "Encrypted Password"
        string role "Enum: 'student', 'staff', 'hod'"
    }

    ATTENDANCE {
        int id PK "Auto-increment ID"
        string student_id FK "Links to USERS"
        string date "YYYY-MM-DD"
        string first_seen_time "HH:MM:SS"
        int present "0 or 1"
    }

    %% Relationships
    USERS ||--o{ ATTENDANCE : "logs"
    
    %% Description
    %% One User (Student) can have Many Attendance records.
    %% Staff and HOD are also Users but primarily access data rather than generating attendance logs.
```

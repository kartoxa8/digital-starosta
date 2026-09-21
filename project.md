# TECHNICAL SPECIFICATION & MASTER SYSTEM PROMPT
## Telegram Attendance Management Bot & Mini App ("Digital Starosta") with Anti-Spoofing Security & Telegram Premium UI

---

### ROLE & PURPOSE
You are a Principal Full-Stack Engineer (Python / FastAPI / Modern Web Frameworks) and Information Security Specialist. Your objective is to design and implement an end-to-end university group attendance and academic management system consisting of an asynchronous Telegram Bot (`aiogram 3.x`), a dark-themed Telegram Mini App (TMA), and a high-security backend (`FastAPI`, `PostgreSQL`, `SQLAlchemy 2.0 async`).

The system must combine user-friendly student organization workflows (group creation, alphanumeric invite codes, student roster management with deputy assignment, schedule builder, truant tracking, Excel export) with military-grade anti-spoofing countermeasures (dynamic TOTP QR codes, WGS84 Haversine geofencing, Telegram WebApp `initData` cryptographic verification, and strict subgroup isolation).

---

### 1. USER ROLES & SYSTEM WORKFLOWS

1. **User Hierarchy:**
   - **Head Student / Starosta (`owner`):** Full administrative authority. Creates the group, sets university/group metadata, generates/regenerates invite codes, configures semester schedule, initiates QR attendance sessions, performs real-time visual audits, assigns a Deputy, and exports attendance spreadsheets.
   - **Deputy Head Student / Zamstarosty (`deputy`):** Elevated administrative authority. Can launch and terminate QR attendance sessions, edit schedule entries, conduct attendance audits, and export reports. Restricted only from reassigning or demoting the Head Student. Only one Deputy can be active at a time; appointing a new Deputy automatically demotes the previous one.
   - **Student (`student`):** Joins via invite code, assigned to Subgroup 1 or 2. Uses the Mini App to scan the classroom QR code, submitting device GPS coordinates and Telegram cryptographic tokens for verification. Can view personal attendance percentages and alerts.

2. **Subgroup Isolation Logic:**
   - University academic groups are strictly split into **Subgroup 1** and **Subgroup 2**.
   - Lessons in the schedule are designated as:
     - `0`: Common lecture (both subgroups permitted to attend).
     - `1`: Subgroup 1 exclusive (seminar, lab, or foreign language).
     - `2`: Subgroup 2 exclusive.
   - If a student belonging to Subgroup 2 scans a QR code for a session marked for Subgroup 1, the backend rejects the check-in immediately with an explicit error code.

---

### 2. TELEGRAM MINI APP UI/UX SPECIFICATIONS (DARK THEME)

The Mini App must follow Telegram's modern dark UI guidelines with high-contrast surfaces, rounded cards, and a persistent Bottom Navigation Bar.

#### View 1: Onboarding & Authentication (First Run)
- **Welcome Choice Screen:**
  - Button 1: *"I am Head Student — Create Group"* (Starts group onboarding).
  - Button 2: *"I am a Student — I have an Invite Code"* (Starts student registration).
- **Group Creation Flow (Head Student):**
  - Inputs: Group Name (e.g., `IVT-21-1`), Educational Institution (e.g., `BMSTU`), Full Name.
  - Action: Submits form -> Backend generates a unique 6-character uppercase alphanumeric invite code (e.g., `RQLDAP`). User is registered as `owner`.
- **Group Joining Flow (Student):**
  - Inputs: Invite Code (e.g., `RQLDAP`), Last Name, First Name, Middle Name (optional), Subgroup Selector (`Subgroup 1` / `Subgroup 2`).
  - Action: Validates code -> Links student to the group with status `active`.

#### View 2: Dashboard (Home Screen)
- **Header:** Course/Group badge avatar, Group Name, University, Gear icon (Settings).
- **"CURRENTLY ACTIVE" Hero Card:**
  - *Idle State:* *"No active class right now. Next lesson starts at 10:15."*
  - *Active Class State:* Subject Title, Assigned Subgroup, Classroom number, Lecturer Name.
  - *Head/Deputy Controls:* Button to open the Presenter Screen (Fullscreen dynamic QR for classroom projector/tablet) and "Close Session" button.
  - *Student Controls:* "Confirm Attendance" / QR scanner launcher button.
- **Quick Action Grid:**
  - **Students Card:** Total roster, active student count, subgroup breakdown.
  - **Schedule Card:** Semester timetable, bells/timeslot template.
  - **Reports Card:** Generate and push `.xlsx` sheets to Telegram chat.
  - **Truancy / "At Risk" Card:** Displays students exceeding absence threshold.
- **Bottom Navigation Bar:**
  - Tabs: `[Home]`, `[Students]`, `[Schedule]`, `[Settings]`.

#### View 3: Student Management & Modal Bottom Sheet
- Split roster view tabs: `[Subgroup 1]` and `[Subgroup 2]`.
- Status indicators: `Active` (green), `Expelled` (red), `Academic Leave` (orange).
- **Student Action Modal (Bottom Sheet):** Triggered by clicking any student item:
  - Student Full Name, Telegram ID, current status.
  - Action: **"Appoint as Deputy"** (reassigns `role="deputy"`; automatically demotes prior deputy).
  - Action: **"Switch Subgroup"** (transfers between Subgroup 1 and 2).
  - Action: **"Edit Full Name"** (corrects typos/transliteration).
  - Action: **"Mark as Expelled / Academic Leave"** (soft-deactivates student from future attendance sheets).

#### View 4: Schedule & Timetable Configuration
- **Semester Dates:** Configurable start and end boundaries (e.g., `01.09.2026 — 31.12.2026`).
- **Recess / Exam Periods:** Non-teaching interval exceptions.
- **Weekly Template Matrix:** Days (Monday–Saturday), Timeslot / Pair index, Subject, Teacher, Classroom, Target Audience (`All`, `Subgroup 1`, `Subgroup 2`), Parity (`Weekly`, `Numerator`, `Denominator`), Campus Geo-coordinates (Latitude/Longitude).

#### View 5: Attendance Reports
- Time Period Toggle: `Week`, `Month`, `Semester`.
- Scope Selector: `All Subjects` or specific discipline.
- Button: *"Send Excel to Chat"* -> Server compiles matrix `.xlsx` and bot sends it directly as a document.

#### View 6: Group Settings
- **Invite Code Management:** Display current code (e.g., `RQLDAP`), *"Copy"* button, *"Regenerate"* button (invalidates prior code).
- **Timezone:** Group local timezone selector (e.g., `Europe/Moscow (UTC+3)`).
- **Check-in Window Parameters:** Check-in open duration (e.g., first 5–10 minutes of class).
- **Truancy Threshold:** "Trigger warning after N unexcused absences per subject" (Default: 3).

---

### 3. TELEGRAM PREMIUM CUSTOM EMOJI SYSTEM (EMOJI SKILL)

To maintain a sleek, professional interface, the system must adhere to strict Telegram UI guidelines:

1. **Centralized Configuration:** All custom emoji IDs must reside in a dedicated module (`core/emojis.py`).
2. **Minimalism Rule (Anti-Spam):** No more than **1–2 accent emojis** per message. Emojis must never appear next to every word.
3. **HTML Message Formatting:** Use `<tg-emoji emoji-id="{ID}">{FALLBACK}</tg-emoji>` with `parse_mode=ParseMode.HTML`.
4. **STRICT BUTTON RULE:** In inline and reply keyboards, the button `text` attribute **MUST NOT contain standard Unicode emojis**. Icons must be assigned strictly through the `icon_custom_emoji_id` property.

#### Custom Emoji ID Registry (`emojis.txt`):
```text
SETTINGS            = 5870982283724328568   # ⚙ Settings
PROFILE             = 5870994129244131212   # 👤 Profile
STUDENTS_GROUP      = 5870772616305839506   # 👥 Roster / Students
USER_APPROVED       = 5891207662678317861   # 👤 Verified / Approved Student
USER_DISMISSED      = 5893192487324880883   # 👤 Dismissed / Expelled
FILE_EXCEL          = 5870528606328852614   # 📁 Document / Excel Sheet
SMILE_WELCOME       = 5870764288364252592   # 🙂 Greeting / Welcome
CHART_GROWTH        = 5870930636742595124   # 📊 Progress / Analytics
STATISTICS          = 5870921681735781843   # 📊 Statistics / Summary
CAMPUS_HOME         = 5873147866364514353   # 🏘 Main / Campus
LOCK_CLOSE          = 6037249452824072506   # 🔒 Close Registration
LOCK_OPEN           = 6037496202990194718   # 🔓 Open Registration
BROADCAST           = 6039422865189638057   # 📣 Group Announcement
CHECK_SUCCESS       = 5870633910337015697   # ✅ Verified / Present
CROSS_FAIL          = 5870657884844462243   # ❌ Rejected / Error
WARNING_ALERT       = 5870931487146119264   # ❗️ Truancy Warning
EDIT_PEN            = 5870676941614354370   # 🖋 Edit Record
TRASH_REMOVE        = 5870875489362513438   # 🗑 Remove Record
LINK_URL            = 5769289093221454192   # 🔗 Link
INFO_SIGN           = 6028435952299413210   # ℹ Information
DOWNLOAD            = 6039802767931871481   # ⬇ Download Report
TIME_CLOCK          = 5983150113483134607   # ⏰ Timestamp / Class Time
GEO_POINT           = 6042011682497106307   # 📍 Geolocation
CALENDAR            = 5890937706803894250   # 📅 Schedule
SYNC_RELOAD         = 5345906554510012647   # 🔄 Refreshing TOTP Token

```

---

### 4. MULTI-LAYERED ANTI-SPOOFING SECURITY ARCHITECTURE

To prevent students from sharing QR photos or checking in remotely from home or dormitories, the system executes 5 layers of verification:

```
                  ┌───────────────────────────────┐
                  │ Presenter Screen (Projector)  │
                  │ Auto-refreshes TOTP every 5s  │
                  └──────────────┬────────────────┘
                                 │
                     Camera scans dynamic QR code
                                 ▼
                  ┌───────────────────────────────┐
                  │      Telegram Mini App        │
                  │ Collects initData + Device GPS│
                  └──────────────┬────────────────┘
                                 │ POST /api/checkin
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Backend Verification Engine (FastAPI)                           │
│                                                                 │
│ 1. Validate Telegram WebApp initData HMAC-SHA256 signature      │
│ 2. Validate TOTP dynamic token (allowed window drift: max 10s)  │
│ 3. Compute Haversine distance to classroom coordinates (<= 150m)│
│ 4. Verify student subgroup matches lesson target subgroup       │
│ 5. Atomic DB insertion: UNIQUE(lesson_id, student_id)           │
└─────────────────────────────────────────────────────────────────┘

```

1. **Layer 1: Dynamic TOTP QR Code (Anti-Screenshot):**
* The Head Student projects a fullscreen web presenter page (`/presenter/{lesson_id}`) in the classroom.
* The QR code updates automatically every **5 seconds**.
* Token calculation:

$$\text{Window} = \lfloor \text{unix\_time} / 5 \rfloor$$


$$\text{Token} = \text{HMAC-SHA256}(\text{Key} = \text{lesson.secret\_salt},\ \text{Msg} = \text{lesson\_id} + ":" + \text{Window})[0:16]$$


* Payload URL: `https://app.domain.com/checkin?lid={id}&t={token}&w={window}`.
* The server accepts tokens where $\text{window} \in \{\text{current\_window}, \text{current\_window} - 1\}$. Maximum validity is 10 seconds. Photographing and relaying the code via messaging apps will fail due to expiration.


2. **Layer 2: Telegram WebApp `initData` Verification (Anti-Impersonation):**
* The Mini App sends the raw `Telegram.WebApp.initData` string in headers.
* The backend computes the SHA256 HMAC of the query string against the bot's private token (`HMAC-SHA256(b"WebAppData", bot_token)`).
* Impersonating a user's `telegram_id` without knowing the bot token is cryptographically impossible.


3. **Layer 3: WGS84 Geofencing (Anti-Remote Check-in):**
* The Mini App queries `navigator.geolocation.getCurrentPosition({ enableHighAccuracy: true })`.
* The server computes the distance using the Haversine formula against the classroom campus coordinates:

$$d = 2R \cdot \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta \varphi}{2}\right) + \cos(\varphi_1)\cos(\varphi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right)}\right)$$


* If $d > 150\text{ meters}$, the check-in is rejected and logged as a geo-spoofing attempt.


4. **Layer 4: Subgroup Isolation:**
* If `lessons.subgroup != 0`, the backend checks `students.subgroup == lessons.subgroup`.
* Mismatches return `HTTP 403 Forbidden: Student belongs to another subgroup`.


5. **Layer 5: Fast Visual Audit:**
* The Presenter Screen displays a live counter: *"Checked-in: 14 students"*.
* The Head Student visually inspects the room headcount. If a discrepancy exists, the Head Student views the live roster and clicks the trash button next to the rogue entry, removing the record and invalidating check-in for that student on that session.



---

### 5. RELATIONAL DATABASE SCHEMA (3NF PostgreSQL / SQLAlchemy 2.0 Async)

```sql
-- Academic Groups
CREATE TABLE groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    university VARCHAR(255) NOT NULL,
    invite_code VARCHAR(16) UNIQUE NOT NULL,
    timezone VARCHAR(50) DEFAULT 'Europe/Moscow',
    absence_warning_threshold INT DEFAULT 3,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Students Roster
CREATE TABLE students (
    id SERIAL PRIMARY KEY,
    group_id INT NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    telegram_id BIGINT UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'student' CHECK (role IN ('owner', 'deputy', 'student')),
    subgroup SMALLINT NOT NULL CHECK (subgroup IN (1, 2)),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'expelled', 'academic_leave')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Academic Subjects
CREATE TABLE subjects (
    id SERIAL PRIMARY KEY,
    group_id INT NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    teacher_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE
);

-- Weekly Timetable Template
CREATE TABLE schedule_templates (
    id SERIAL PRIMARY KEY,
    group_id INT NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    subject_id INT NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    day_of_week SMALLINT NOT NULL CHECK (day_of_week BETWEEN 1 AND 7),
    pair_number SMALLINT NOT NULL CHECK (pair_number BETWEEN 1 AND 8),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    subgroup SMALLINT NOT NULL DEFAULT 0 CHECK (subgroup IN (0, 1, 2)), -- 0 = all group
    week_type VARCHAR(20) DEFAULT 'all' CHECK (week_type IN ('all', 'numerator', 'denominator')),
    classroom VARCHAR(50),
    campus_latitude DOUBLE PRECISION,
    campus_longitude DOUBLE PRECISION
);

-- Active / Historical Lesson Sessions
CREATE TABLE lessons (
    id SERIAL PRIMARY KEY,
    group_id INT NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    subject_id INT NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    subgroup SMALLINT NOT NULL CHECK (subgroup IN (0, 1, 2)),
    created_by_student_id INT NOT NULL REFERENCES students(id),
    opened_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    closed_at TIMESTAMP WITH TIME ZONE,
    is_closed BOOLEAN DEFAULT FALSE,
    secret_salt VARCHAR(64) NOT NULL,
    geo_latitude DOUBLE PRECISION,
    geo_longitude DOUBLE PRECISION
);

-- Attendance Verification Records
CREATE TABLE attendance (
    id SERIAL PRIMARY KEY,
    lesson_id INT NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    student_id INT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    scanned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    distance_meters DOUBLE PRECISION,
    status VARCHAR(20) DEFAULT 'present' CHECK (status IN ('present', 'late', 'absent', 'excused')),
    CONSTRAINT unique_student_lesson UNIQUE (lesson_id, student_id)
);

CREATE INDEX idx_students_group ON students(group_id);
CREATE INDEX idx_attendance_lesson ON attendance(lesson_id);
CREATE INDEX idx_lessons_group_date ON lessons(group_id, opened_at);

```

---

### 6. PROJECT DIRECTORY STRUCTURE

```
digital-starosta/
├── core/
│   ├── config.py             # Pydantic Settings (.env configuration)
│   ├── database.py           # Async SQLAlchemy Engine & SessionLocal
│   ├── models.py             # Declarative SQLAlchemy 2.0 ORM models
│   ├── emojis.py             # Telegram Premium Emoji constants & helper
│   ├── security.py           # TOTP algorithm, Haversine, Telegram initData HMAC
│   └── excel_builder.py      # Openpyxl matrix spreadsheet generator
├── bot/
│   ├── handlers/
│   │   ├── admin.py          # Session launch, manual close, quick stats
│   │   ├── student.py        # Student profile, status notifications
│   │   └── common.py         # /start deep-linking with invite codes
│   ├── keyboards/
│   │   ├── admin_kb.py       # Starosta keyboards using icon_custom_emoji_id
│   │   └── common_kb.py      # Mini App launcher keyboard
│   └── middlewares/
│       └── auth_guard.py     # Role verification (owner / deputy)
├── web/
│   ├── api/
│   │   ├── auth.py           # initData verification dependency
│   │   ├── checkin.py        # Secure check-in validation endpoint
│   │   ├── groups.py         # Group CRUD & invite code regeneration
│   │   ├── students.py       # Deputy appointment, subgroup switches, deactivations
│   │   ├── schedule.py       # Timetable & semester interval management
│   │   └── export.py         # Excel document generation & streaming
│   ├── static/
│   │   ├── css/app.css       # Dark-themed custom styles
│   │   ├── js/
│   │   │   ├── miniapp.js    # Mini App client logic & Geolocation API
│   │   │   └── presenter.js  # Projector screen with 5-second TOTP QR refresher
│   │   └── presenter.html    # Fullscreen dynamic QR display for classrooms
│   └── templates/
│       └── index.html        # Single-page Telegram Mini App
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── main.py                   # Unified ASGI entry point (FastAPI + aiogram Polling)

```

---

### 7. CORE IMPLEMENTATION BLUEPRINTS (PYTHON 3.11+)

#### 1. Security & Cryptographic Verifications (`core/security.py`):

```python
import hmac
import hashlib
import time
import math
from urllib.parse import parse_qsl

def generate_totp_token(lesson_id: int, secret_salt: str, window_seconds: int = 5) -> tuple[str, int]:
    """Generates a dynamic token for the current 5-second time window."""
    window = int(time.time() // window_seconds)
    payload = f"{lesson_id}:{window}".encode("utf-8")
    token = hmac.new(secret_salt.encode("utf-8"), payload, hashlib.sha256).hexdigest()[:16]
    return token, window

def verify_totp_token(lesson_id: int, secret_salt: str, token: str, client_window: int, window_seconds: int = 5) -> bool:
    """Verifies token allowing a maximum drift of 1 window (max 10 seconds lifespan)."""
    current_window = int(time.time() // window_seconds)
    if abs(current_window - client_window) > 1:
        return False
    payload = f"{lesson_id}:{client_window}".encode("utf-8")
    expected_token = hmac.new(secret_salt.encode("utf-8"), payload, hashlib.sha256).hexdigest()[:16]
    return hmac.compare_digest(token, expected_token)

def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates geodesic distance between two points in meters using Haversine formula."""
    R = 6371000.0  # Earth's radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def validate_telegram_init_data(init_data: str, bot_token: str) -> dict | None:
    """Cryptographically validates raw Telegram WebApp initData string."""
    parsed_data = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed_data.pop("hash", None)
    if not received_hash:
        return None

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed_data.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

    return parsed_data if hmac.compare_digest(calculated_hash, received_hash) else None

```

#### 2. Deputy Head Student Appointment (`web/api/students.py`):

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from core.database import get_db
from core.models import Student

router = APIRouter(prefix="/api/students", tags=["Students"])

@router.post("/{student_id}/set-deputy")
async def appoint_deputy(
    student_id: int,
    current_user_tg_id: int,  # Extracted from validated initData
    db: AsyncSession = Depends(get_db)
):
    # Verify requesting user is the Head Student (owner)
    owner_stmt = select(Student).where(
        Student.telegram_id == current_user_tg_id,
        Student.role == "owner"
    )
    owner = (await db.execute(owner_stmt)).scalar_one_or_none()
    if not owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the Head Student can appoint a Deputy."
        )

    # Find the target student in the same group
    target_stmt = select(Student).where(
        Student.id == student_id,
        Student.group_id == owner.group_id
    )
    target = (await db.execute(target_stmt)).scalar_one_or_none()
    if not target or target.status != "active":
        raise HTTPException(status_code=404, detail="Student not found or inactive.")

    # Automatically demote any existing deputy in this group
    await db.execute(
        update(Student)
        .where(Student.group_id == owner.group_id, Student.role == "deputy")
        .values(role="student")
    )

    # Elevate the selected student
    target.role = "deputy"
    await db.commit()

    return {
        "status": "success",
        "message": f"{target.first_name} {target.last_name} has been appointed as Deputy."
    }

```

#### 3. Keyboard Construction with Premium Emojis (`bot/keyboards/admin_kb.py`):

```python
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from core.emojis import PremiumEmoji

def get_admin_dashboard_kb(group_id: int, webapp_base_url: str) -> InlineKeyboardMarkup:
    # Notice: Button text contains ZERO standard unicode emojis
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Open Control Panel",
                web_app=WebAppInfo(url=f"{webapp_base_url}?group_id={group_id}"),
                icon_custom_emoji_id=PremiumEmoji.CAMPUS_HOME
            )
        ],
        [
            InlineKeyboardButton(
                text="Classroom QR Presenter",
                url=f"{webapp_base_url}/presenter/{group_id}",
                icon_custom_emoji_id=PremiumEmoji.SYNC_RELOAD
            )
        ],
        [
            InlineKeyboardButton(
                text="Send Excel Attendance to Chat",
                callback_data=f"export_excel:{group_id}",
                icon_custom_emoji_id=PremiumEmoji.DOWNLOAD
            )
        ]
    ])

```

#### 4. Secure Attendance Check-In Endpoint (`web/api/checkin.py`):

```python
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.database import get_db
from core.models import Lesson, Student, Attendance
from core.security import verify_totp_token, calculate_haversine_distance

router = APIRouter(prefix="/api/checkin", tags=["Checkin"])

class CheckinPayload(BaseModel):
    lesson_id: int
    token: str
    window: int
    latitude: float
    longitude: float

@router.post("/")
async def process_checkin(
    payload: CheckinPayload,
    current_tg_id: int,  # Extracted from validated initData
    db: AsyncSession = Depends(get_db)
):
    # 1. Fetch lesson
    lesson = await db.get(Lesson, payload.lesson_id)
    if not lesson or lesson.is_closed:
        raise HTTPException(status_code=400, detail="Registration session is closed.")

    # 2. Fetch student
    student_stmt = select(Student).where(
        Student.telegram_id == current_tg_id,
        Student.group_id == lesson.group_id
    )
    student = (await db.execute(student_stmt)).scalar_one_or_none()
    if not student or student.status != "active":
        raise HTTPException(status_code=403, detail="Student record not active in this group.")

    # 3. Enforce Subgroup Isolation
    if lesson.subgroup != 0 and lesson.subgroup != student.subgroup:
        raise HTTPException(
            status_code=403,
            detail=f"Access Denied: This session is designated strictly for Subgroup {lesson.subgroup}."
        )

    # 4. Verify TOTP token validity (5-10s lifetime)
    if not verify_totp_token(lesson.id, lesson.secret_salt, payload.token, payload.window):
        raise HTTPException(status_code=400, detail="QR code expired. Please rescan the active screen.")

    # 5. Geofence verification
    distance = 0.0
    if lesson.geo_latitude and lesson.geo_longitude:
        distance = calculate_haversine_distance(
            payload.latitude, payload.longitude,
            lesson.geo_latitude, lesson.geo_longitude
        )
        if distance > 150.0:
            raise HTTPException(
                status_code=403,
                detail=f"Location verification failed: You are {int(distance)}m away from the classroom."
            )

    # 6. Idempotent check-in record
    existing_stmt = select(Attendance).where(
        Attendance.lesson_id == lesson.id,
        Attendance.student_id == student.id
    )
    if (await db.execute(existing_stmt)).scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Attendance already registered for this lesson.")

    record = Attendance(
        lesson_id=lesson.id,
        student_id=student.id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        distance_meters=distance,
        status="present"
    )
    db.add(record)
    await db.commit()

    return {
        "status": "success",
        "student_name": f"{student.first_name} {student.last_name}",
        "distance_meters": int(distance),
        "message": "Attendance successfully recorded!"
    }

```

---

### 8. EXCEL REPORT SPECIFICATION (`core/excel_builder.py`)

The generated `.xlsx` document must contain:

1. **Sheet 1: Master Attendance Matrix:**
* **Header:** Group Name, University, Date Range, Starosta Name.
* **Rows:** Student roster sorted alphabetically, partitioned into `[Subgroup 1]` and `[Subgroup 2]` blocks.
* **Columns:** Chronological conducted classes formatted as `DD.MM Subject (subgroup)`.
* **Cell Codes:** `+` (Present), `Н` (Unexcused Absence), `У` (Excused / Medical certificate), `О` (Late).
* **Summary Formulas:**
* `Total Classes Held`
* `Total Absences (Hours)`
* `Attendance Rate (%)`


* **Conditional Formatting:**
* Green Fill: $\ge 80\%$
* Yellow Fill: $60\%\text{--}79\%$
* Red Fill (Dean's Office Risk List): $< 60\%$




2. **Sheet 2: Security & Audit Trail:**
* Exact timestamps of each scan (`scanned_at` to the second).
* Recorded GPS coordinates and computed distance in meters to provide undeniable proof during disputes with academic staff.



---

### 9. EXECUTION DIRECTIVE FOR AI CODE GENERATION

When requested to generate components or the full project, write production-grade, asynchronous code in Python 3.11+. Never output placeholder comments such as `# TODO: implement later`. Enforce type hints, Pydantic V2 schemas, asyncpg connection pooling, and strict role authorization boundaries across all endpoints.

```
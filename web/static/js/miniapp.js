const tg = window.Telegram?.WebApp;
tg?.ready();
tg?.expand();

let state = {
  registered: false,
  currentUser: null,
  currentGroup: null,
  students: [],
  activeLesson: null,
  subjects: [],
  templates: [],
  currentSubgroupFilter: 1,
  selectedStudent: null,
};

function getHeaders() {
  const headers = { "Content-Type": "application/json" };
  if (tg?.initData) {
    headers["X-Telegram-Init-Data"] = tg.initData;
  }
  return headers;
}

// Initialization
async function init() {
  try {
    // Check if deep link invite code in URL
    const urlParams = new URLSearchParams(window.location.search);
    const joinCodeParam = urlParams.get("join");
    if (joinCodeParam) {
      const codeField = document.getElementById("join-code");
      if (codeField) codeField.value = joinCodeParam;
    }

    const res = await fetch("/api/groups/me", { headers: getHeaders() });
    if (!res.ok) {
      showOnboarding();
      return;
    }
    const data = await res.json();
    if (!data.registered) {
      showOnboarding();
    } else {
      state.registered = true;
      state.currentUser = data.student;
      state.currentGroup = data.group;
      showApp();
      await refreshAllData();
    }
  } catch (err) {
    console.error("Init failed:", err);
    showOnboarding();
  }
}

function showOnboarding() {
  document.querySelectorAll(".view").forEach((v) => (v.style.display = "none"));
  const ob = document.getElementById("view-onboarding");
  if (ob) ob.style.display = "block";
  const nav = document.querySelector(".bottom-nav");
  if (nav) nav.style.display = "none";
}

function showApp() {
  const ob = document.getElementById("view-onboarding");
  if (ob) ob.style.display = "none";
  const nav = document.querySelector(".bottom-nav");
  if (nav) nav.style.display = "flex";

  // Update header
  const title = document.getElementById("group-title");
  const sub = document.getElementById("group-subtitle");
  const avatar = document.getElementById("group-avatar");
  if (title) title.textContent = state.currentGroup.name;
  if (sub) sub.textContent = state.currentGroup.university;
  if (avatar) avatar.textContent = state.currentGroup.name.slice(0, 2).toUpperCase();

  // Role-based visibility
  const isAdmin = state.currentUser.role === "owner" || state.currentUser.role === "deputy";
  const isOwner = state.currentUser.role === "owner";

  const quickLaunch = document.getElementById("admin-quick-launch");
  const btnAddSubject = document.getElementById("btn-add-subject");
  const btnRegen = document.getElementById("btn-regen-code");
  const btnSaveSettings = document.getElementById("btn-save-settings");

  if (quickLaunch) quickLaunch.style.display = isAdmin ? "block" : "none";
  if (btnAddSubject) btnAddSubject.style.display = isAdmin ? "block" : "none";
  if (btnRegen) btnRegen.style.display = isOwner ? "block" : "none";
  if (btnSaveSettings) btnSaveSettings.style.display = isAdmin ? "block" : "none";

  // Populate settings fields
  const inviteCodeIn = document.getElementById("settings-invite-code");
  const timezoneIn = document.getElementById("settings-timezone");
  const thresholdIn = document.getElementById("settings-threshold");
  if (inviteCodeIn) inviteCodeIn.value = state.currentGroup.invite_code;
  if (timezoneIn) timezoneIn.value = state.currentGroup.timezone;
  if (thresholdIn) thresholdIn.value = state.currentGroup.absence_warning_threshold;

  switchTab("tab-home");
}

async function refreshAllData() {
  await Promise.all([
    fetchActiveLesson(),
    fetchStudents(),
    fetchSubjects(),
    fetchTemplates(),
  ]);
  updateDashboardStats();
}

// Navigation Tabs
function switchTab(tabId) {
  document.querySelectorAll(".view").forEach((v) => (v.style.display = "none"));
  const target = document.getElementById(tabId);
  if (target) target.style.display = "block";

  document.querySelectorAll(".nav-item").forEach((btn) => {
    btn.classList.toggle("active", btn.getAttribute("onclick")?.includes(tabId));
  });

  if (tabId === "tab-students") {
    renderRoster();
  } else if (tabId === "tab-schedule") {
    renderSchedule();
  }
}

function switchOnboardingMode(mode) {
  const formJoin = document.getElementById("form-join");
  const formCreate = document.getElementById("form-create");
  const btnJoin = document.getElementById("btn-tab-join");
  const btnCreate = document.getElementById("btn-tab-create");

  if (mode === "join") {
    formJoin.style.display = "block";
    formCreate.style.display = "none";
    btnJoin.classList.add("active");
    btnCreate.classList.remove("active");
  } else {
    formJoin.style.display = "none";
    formCreate.style.display = "block";
    btnCreate.classList.add("active");
    btnJoin.classList.remove("active");
  }
}

// Onboarding actions
async function submitJoinGroup() {
  const payload = {
    invite_code: document.getElementById("join-code").value.trim().toUpperCase(),
    last_name: document.getElementById("join-lastname").value.trim(),
    first_name: document.getElementById("join-firstname").value.trim(),
    middle_name: document.getElementById("join-middlename").value.trim() || null,
    subgroup: parseInt(document.getElementById("join-subgroup").value, 10),
  };

  if (!payload.invite_code || !payload.last_name || !payload.first_name) {
    showAlert("Please fill in invite code, last name, and first name.");
    return;
  }

  try {
    const res = await fetch("/api/groups/join", {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) {
      showAlert(data.detail || "Failed to join group.");
      return;
    }
    showAlert(`Successfully joined group: ${data.group_name}`);
    await init();
  } catch (e) {
    showAlert("Network error while joining group.");
  }
}

async function submitCreateGroup() {
  const payload = {
    name: document.getElementById("create-group-name").value.trim(),
    university: document.getElementById("create-university").value.trim(),
    last_name: document.getElementById("create-lastname").value.trim(),
    first_name: document.getElementById("create-firstname").value.trim(),
    subgroup: parseInt(document.getElementById("create-subgroup").value, 10),
  };

  if (!payload.name || !payload.university || !payload.last_name || !payload.first_name) {
    showAlert("Please fill in all group details.");
    return;
  }

  try {
    const res = await fetch("/api/groups", {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) {
      showAlert(data.detail || "Failed to create group.");
      return;
    }
    showAlert(`Group created! Invite code: ${data.invite_code}`);
    await init();
  } catch (e) {
    showAlert("Network error while creating group.");
  }
}

// Active Lesson & Dashboard
async function fetchActiveLesson() {
  if (!state.currentGroup) return;
  try {
    const res = await fetch(`/api/schedule/groups/${state.currentGroup.id}/active-lesson`, {
      headers: getHeaders(),
    });
    if (!res.ok) return;
    const data = await res.json();
    state.activeLesson = data.has_active ? data.lesson : null;
    renderActiveLessonHero();
  } catch (e) {
    console.error("fetchActiveLesson error:", e);
  }
}

function renderActiveLessonHero() {
  const statusTag = document.getElementById("lesson-status-tag");
  const title = document.getElementById("active-subject-title");
  const desc = document.getElementById("active-lesson-desc");
  const adminControls = document.getElementById("admin-lesson-controls");
  const studentControls = document.getElementById("student-checkin-controls");
  const presenterLink = document.getElementById("presenter-link");

  const isAdmin = state.currentUser?.role === "owner" || state.currentUser?.role === "deputy";

  if (!state.activeLesson) {
    if (statusTag) statusTag.textContent = "IDLE";
    if (title) title.textContent = "No active class right now";
    if (desc) desc.textContent = "Your group schedule will appear once an attendance session is started.";
    if (adminControls) adminControls.style.display = "none";
    if (studentControls) studentControls.style.display = "none";
  } else {
    const l = state.activeLesson;
    const sgText = l.subgroup === 0 ? "All Group" : `Subgroup ${l.subgroup}`;
    if (statusTag) statusTag.textContent = "IN PROGRESS";
    if (title) title.textContent = `${l.subject_name}`;
    if (desc) desc.textContent = `Audience: ${sgText} • Teacher: ${l.teacher_name || "Assigned"}`;

    if (isAdmin) {
      if (adminControls) adminControls.style.display = "block";
      if (presenterLink) presenterLink.href = `/presenter/${l.id}`;
    } else {
      if (adminControls) adminControls.style.display = "none";
    }

    if (studentControls) {
      studentControls.style.display = "block";
    }
  }
}

async function closeCurrentLesson() {
  if (!state.activeLesson) return;
  try {
    const res = await fetch(`/api/schedule/lessons/${state.activeLesson.id}/close`, {
      method: "POST",
      headers: getHeaders(),
    });
    if (res.ok) {
      showAlert("Session closed successfully.");
      await fetchActiveLesson();
    } else {
      const d = await res.json();
      showAlert(d.detail || "Failed to close session.");
    }
  } catch (e) {
    showAlert("Error closing session.");
  }
}

// Students Roster
async function fetchStudents() {
  if (!state.currentGroup) return;
  try {
    const res = await fetch(`/api/students/group/${state.currentGroup.id}`, { headers: getHeaders() });
    if (!res.ok) return;
    state.students = await res.json();
  } catch (e) {
    console.error("fetchStudents error:", e);
  }
}

function switchRosterSubgroup(sg) {
  state.currentSubgroupFilter = sg;
  document.getElementById("tab-btn-sg1")?.classList.toggle("active", sg === 1);
  document.getElementById("tab-btn-sg2")?.classList.toggle("active", sg === 2);
  renderRoster();
}

function renderRoster() {
  const listEl = document.getElementById("roster-list");
  if (!listEl) return;

  const filtered = state.students.filter((s) => s.subgroup === state.currentSubgroupFilter);
  if (filtered.length === 0) {
    listEl.innerHTML = `<div class="card" style="text-align:center; color:var(--text-muted);">No students in Subgroup ${state.currentSubgroupFilter}</div>`;
    return;
  }

  listEl.innerHTML = filtered
    .map((s) => {
      const roleBadge = s.role !== "student" ? `<span class="badge badge-${s.role}">${s.role}</span>` : "";
      const statusBadge = `<span class="badge badge-${s.status}">${s.status}</span>`;
      return `
      <div class="student-item" onclick='openStudentModal(${JSON.stringify(s).replace(/'/g, "&#39;")})'>
        <div class="student-info">
          <span class="student-name">${s.last_name} ${s.first_name}</span>
          <span class="student-meta">Rate: ${s.attendance_rate}% • Absences: ${s.absences}</span>
        </div>
        <div style="display:flex; gap:6px; align-items:center;">
          ${roleBadge}
          ${statusBadge}
        </div>
      </div>
    `;
    })
    .join("");
}

function updateDashboardStats() {
  const activeCount = state.students.filter((s) => s.status === "active").length;
  const atRiskCount = state.students.filter((s) => s.at_risk).length;

  const statStudents = document.getElementById("stat-students-count");
  const statAtRisk = document.getElementById("stat-at-risk-count");
  const statSched = document.getElementById("stat-schedule-count");
  const statRate = document.getElementById("stat-attendance-rate");

  if (statStudents) statStudents.textContent = `${activeCount} / ${state.students.length}`;
  if (statAtRisk) statAtRisk.textContent = atRiskCount;
  if (statSched) statSched.textContent = state.templates.length;

  if (state.students.length > 0) {
    const avg = Math.round(state.students.reduce((acc, s) => acc + s.attendance_rate, 0) / state.students.length);
    if (statRate) statRate.textContent = `${avg}%`;
  }
}

function filterAtRiskStudents() {
  switchTab("tab-students");
}

// Student Modal (Bottom Sheet)
function openStudentModal(student) {
  state.selectedStudent = student;
  const modal = document.getElementById("student-modal");
  const nameEl = document.getElementById("modal-student-name");
  const metaEl = document.getElementById("modal-student-meta");
  const actionsEl = document.getElementById("modal-actions-container");

  nameEl.textContent = `${student.last_name} ${student.first_name} ${student.middle_name || ""}`;
  metaEl.textContent = `Subgroup ${student.subgroup} • ${student.role.toUpperCase()} • ${student.status} • Rate: ${student.attendance_rate}%`;

  const isOwner = state.currentUser?.role === "owner";
  const isAdmin = isOwner || state.currentUser?.role === "deputy";

  let html = "";
  if (isAdmin) {
    if (isOwner && student.role !== "owner") {
      if (student.role !== "deputy") {
        html += `<button class="btn btn-secondary" onclick="appointDeputy(${student.id})">Appoint as Deputy Head</button>`;
      }
    }

    const nextSg = student.subgroup === 1 ? 2 : 1;
    html += `<button class="btn btn-secondary" onclick="switchSubgroup(${student.id}, ${nextSg})">Switch to Subgroup ${nextSg}</button>`;
    html += `<button class="btn btn-secondary" onclick="editStudentName(${student.id})">Edit Full Name</button>`;

    if (student.status === "active") {
      html += `<button class="btn btn-secondary" onclick="changeStatus(${student.id}, 'academic_leave')">Set Academic Leave</button>`;
      html += `<button class="btn btn-danger" onclick="changeStatus(${student.id}, 'expelled')">Mark as Expelled</button>`;
    } else {
      html += `<button class="btn btn-secondary" onclick="changeStatus(${student.id}, 'active')">Restore to Active</button>`;
    }
  } else {
    html = `<p style="color:var(--text-muted); font-size:13px; text-align:center;">Only administrators can modify student records.</p>`;
  }

  actionsEl.innerHTML = html;
  modal.classList.add("active");
}

function closeStudentModal() {
  document.getElementById("student-modal")?.classList.remove("active");
}

async function appointDeputy(studentId) {
  try {
    const res = await fetch(`/api/students/${studentId}/set-deputy`, {
      method: "POST",
      headers: getHeaders(),
    });
    const d = await res.json();
    if (res.ok) {
      showAlert(d.message || "Deputy appointed successfully.");
      closeStudentModal();
      await fetchStudents();
      renderRoster();
    } else {
      showAlert(d.detail || "Failed to appoint deputy.");
    }
  } catch (e) {
    showAlert("Error appointing deputy.");
  }
}

async function switchSubgroup(studentId, newSubgroup) {
  try {
    const res = await fetch(`/api/students/${studentId}`, {
      method: "PATCH",
      headers: getHeaders(),
      body: JSON.stringify({ subgroup: newSubgroup }),
    });
    if (res.ok) {
      showAlert(`Transferred to Subgroup ${newSubgroup}`);
      closeStudentModal();
      await fetchStudents();
      renderRoster();
    } else {
      const d = await res.json();
      showAlert(d.detail || "Failed to transfer subgroup.");
    }
  } catch (e) {
    showAlert("Error transferring subgroup.");
  }
}

async function editStudentName(studentId) {
  const current = state.selectedStudent;
  const newLast = prompt("Last name:", current.last_name);
  if (newLast === null) return;
  const newFirst = prompt("First name:", current.first_name);
  if (newFirst === null) return;

  try {
    const res = await fetch(`/api/students/${studentId}`, {
      method: "PATCH",
      headers: getHeaders(),
      body: JSON.stringify({ last_name: newLast, first_name: newFirst }),
    });
    if (res.ok) {
      showAlert("Name updated.");
      closeStudentModal();
      await fetchStudents();
      renderRoster();
    }
  } catch (e) {
    showAlert("Error updating name.");
  }
}

async function changeStatus(studentId, newStatus) {
  try {
    const res = await fetch(`/api/students/${studentId}`, {
      method: "PATCH",
      headers: getHeaders(),
      body: JSON.stringify({ status: newStatus }),
    });
    if (res.ok) {
      showAlert(`Status updated to ${newStatus}`);
      closeStudentModal();
      await fetchStudents();
      renderRoster();
    }
  } catch (e) {
    showAlert("Error updating status.");
  }
}

// Subjects & Schedule
async function fetchSubjects() {
  if (!state.currentGroup) return;
  try {
    const res = await fetch(`/api/schedule/groups/${state.currentGroup.id}/subjects`, { headers: getHeaders() });
    if (!res.ok) return;
    state.subjects = await res.json();
    populateSubjectDropdowns();
  } catch (e) {
    console.error("fetchSubjects error:", e);
  }
}

function populateSubjectDropdowns() {
  const select = document.getElementById("quick-launch-subject");
  if (!select) return;
  select.innerHTML = state.subjects.map((s) => `<option value="${s.id}">${s.name}</option>`).join("");
}

async function fetchTemplates() {
  if (!state.currentGroup) return;
  try {
    const res = await fetch(`/api/schedule/groups/${state.currentGroup.id}/templates`, { headers: getHeaders() });
    if (!res.ok) return;
    state.templates = await res.json();
  } catch (e) {
    console.error("fetchTemplates error:", e);
  }
}

function renderSchedule() {
  const container = document.getElementById("schedule-matrix");
  if (!container) return;

  if (state.templates.length === 0) {
    container.innerHTML = `<p style="color:var(--text-muted); font-size:13px; text-align:center;">No timetable templates configured yet.</p>`;
    return;
  }

  const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
  let html = "";

  for (let d = 1; d <= 7; d++) {
    const dayTemplates = state.templates.filter((t) => t.day_of_week === d);
    if (dayTemplates.length === 0) continue;

    html += `<h3 style="font-size:14px; margin: 12px 0 6px; color:var(--accent);">${days[d - 1]}</h3>`;
    dayTemplates.forEach((t) => {
      const sgText = t.subgroup === 0 ? "All" : `Subgroup ${t.subgroup}`;
      html += `
        <div style="background:#13151b; border:1px solid var(--card-border); border-radius:10px; padding:10px 12px; margin-bottom:6px;">
          <div style="display:flex; justify-content:space-between; font-size:13px; font-weight:600;">
            <span>Pair ${t.pair_number} (${t.start_time} - ${t.end_time})</span>
            <span class="badge badge-active">${sgText}</span>
          </div>
          <div style="font-size:14px; margin-top:2px;">${t.subject_name}</div>
          <div style="font-size:12px; color:var(--text-muted);">${t.classroom ? "Room " + t.classroom + " • " : ""}${t.teacher_name || ""}</div>
        </div>
      `;
    });
  }

  container.innerHTML = html;
}

async function launchLessonSession() {
  const subjId = parseInt(document.getElementById("quick-launch-subject").value, 10);
  const sg = parseInt(document.getElementById("quick-launch-subgroup").value, 10);

  if (!subjId) {
    showAlert("Please select a subject.");
    return;
  }

  try {
    const res = await fetch(`/api/schedule/groups/${state.currentGroup.id}/lessons`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ subject_id: subjId, subgroup: sg }),
    });
    const d = await res.json();
    if (res.ok) {
      showAlert("Attendance session launched!");
      await fetchActiveLesson();
      if (d.presenter_url) {
        window.open(d.presenter_url, "_blank");
      }
    } else {
      showAlert(d.detail || "Failed to start session.");
    }
  } catch (e) {
    showAlert("Error starting session.");
  }
}

function openAddSubjectModal() {
  document.getElementById("subject-modal")?.classList.add("active");
}

function closeSubjectModal() {
  document.getElementById("subject-modal")?.classList.remove("active");
}

async function submitNewSubject() {
  const name = document.getElementById("new-subject-name").value.trim();
  const teacher = document.getElementById("new-subject-teacher").value.trim();
  if (!name) {
    showAlert("Subject name is required.");
    return;
  }

  try {
    const res = await fetch("/api/schedule/subjects", {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ group_id: state.currentGroup.id, name, teacher_name: teacher || null }),
    });
    if (res.ok) {
      showAlert("Subject added!");
      closeSubjectModal();
      await fetchSubjects();
    } else {
      const d = await res.json();
      showAlert(d.detail || "Failed to add subject.");
    }
  } catch (e) {
    showAlert("Error adding subject.");
  }
}

// QR Code Scanning with GPS verification
function triggerQrScan() {
  if (tg && tg.showScanQrPopup) {
    tg.showScanQrPopup({ text: "Point camera at classroom presenter QR code" }, async (text) => {
      await processQrPayload(text);
      tg.closeScanQrPopup();
      return true;
    });
  } else {
    // Web fallback for testing without Telegram client
    const text = prompt("Enter QR Code URL / Text:");
    if (text) {
      processQrPayload(text);
    }
  }
}

async function processQrPayload(qrText) {
  try {
    const url = new URL(qrText);
    const lessonId = parseInt(url.searchParams.get("lid"), 10);
    const token = url.searchParams.get("t");
    const windowVal = parseInt(url.searchParams.get("w"), 10);

    if (!lessonId || !token || isNaN(windowVal)) {
      showAlert("Invalid classroom QR code.");
      return;
    }

    if (!navigator.geolocation) {
      showAlert("Geolocation is not supported by your browser/device.");
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        try {
          const res = await fetch("/api/checkin", {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({
              lesson_id: lessonId,
              token,
              window: windowVal,
              latitude: pos.coords.latitude,
              longitude: pos.coords.longitude,
            }),
          });
          const d = await res.json();
          if (res.ok) {
            showAlert(`✅ Attendance Verified! (${d.distance_meters}m from classroom)`);
            await refreshAllData();
          } else {
            showAlert(`❌ ${d.detail || "Verification failed."}`);
          }
        } catch (e) {
          showAlert("Network error during check-in.");
        }
      },
      (err) => {
        showAlert("Classroom check-in requires location access to verify classroom presence.");
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  } catch (e) {
    showAlert("Could not parse QR payload.");
  }
}

// Reports & Settings
function downloadExcel() {
  if (!state.currentGroup) return;
  window.open(`/api/export/group/${state.currentGroup.id}`, "_blank");
}

function copyInviteCode() {
  const code = document.getElementById("settings-invite-code").value;
  navigator.clipboard.writeText(code);
  showAlert(`Copied invite code: ${code}`);
}

async function regenerateInviteCode() {
  if (!confirm("Regenerating the invite code will invalidate the previous code. Proceed?")) return;
  try {
    const res = await fetch(`/api/groups/${state.currentGroup.id}/regenerate-code`, {
      method: "POST",
      headers: getHeaders(),
    });
    const d = await res.json();
    if (res.ok) {
      state.currentGroup.invite_code = d.invite_code;
      document.getElementById("settings-invite-code").value = d.invite_code;
      showAlert(`New invite code generated: ${d.invite_code}`);
    } else {
      showAlert(d.detail || "Failed to regenerate code.");
    }
  } catch (e) {
    showAlert("Error regenerating invite code.");
  }
}

async function saveGroupSettings() {
  const tz = document.getElementById("settings-timezone").value;
  const th = parseInt(document.getElementById("settings-threshold").value, 10);

  try {
    const res = await fetch(`/api/groups/${state.currentGroup.id}`, {
      method: "PATCH",
      headers: getHeaders(),
      body: JSON.stringify({ timezone: tz, absence_warning_threshold: th }),
    });
    if (res.ok) {
      showAlert("Group settings updated successfully.");
      state.currentGroup.timezone = tz;
      state.currentGroup.absence_warning_threshold = th;
    } else {
      const d = await res.json();
      showAlert(d.detail || "Failed to save settings.");
    }
  } catch (e) {
    showAlert("Error saving settings.");
  }
}

function showAlert(msg) {
  if (tg?.showAlert) {
    tg.showAlert(msg);
  } else {
    alert(msg);
  }
}

window.addEventListener("DOMContentLoaded", init);

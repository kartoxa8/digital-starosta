const lessonId = location.pathname.split("/").pop();
const qrEl = document.getElementById("qr");
const countEl = document.getElementById("count");
const titleEl = document.getElementById("session-title");
const tbodyEl = document.getElementById("attendees-tbody");

// qrcodejs instance — created once, updated via makeCode()
let qrInstance = null;

function renderQR(payload) {
  if (!qrInstance) {
    qrInstance = new QRCode(qrEl, {
      text: payload,
      width: 260,
      height: 260,
      colorDark: "#0f1115",
      colorLight: "#ffffff",
      correctLevel: QRCode.CorrectLevel.M,
    });
  } else {
    qrInstance.makeCode(payload);
  }
  qrEl.style.opacity = "1";
}

async function refreshPresenter() {
  try {
    const res = await fetch(`/api/presenter/${lessonId}`);
    if (!res.ok) return;
    const d = await res.json();

    if (d.closed) {
      titleEl.textContent = "Attendance Session Closed";
      countEl.textContent = "Final Attendance: " + (d.count || 0);
      qrEl.style.opacity = "0.2";
      return;
    }

    countEl.textContent = `Checked in: ${d.count} students`;
    const payload = `${location.origin}/checkin?lid=${d.lesson_id}&t=${d.token}&w=${d.window}`;
    renderQR(payload);
  } catch (err) {
    console.error("refreshPresenter error:", err);
  }
}

async function refreshAttendees() {
  try {
    const res = await fetch(`/api/presenter/${lessonId}/attendees`);
    if (!res.ok) return;
    const list = await res.json();

    if (!list || list.length === 0) {
      tbodyEl.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">Waiting for check-ins...</td></tr>`;
      return;
    }

    tbodyEl.innerHTML = list
      .map(
        (item) => `
      <tr>
        <td style="font-weight: 600;">${item.student_name}</td>
        <td>Subgroup ${item.subgroup}</td>
        <td style="color: var(--text-muted);">${item.scanned_at}</td>
        <td><span class="badge badge-active">${item.distance_meters !== null ? item.distance_meters + "m" : "OK"}</span></td>
        <td style="text-align: right;">
          <button class="trash-btn" onclick="removeAttendee(${item.id})" title="Remove attendance record">🗑️</button>
        </td>
      </tr>
    `
      )
      .join("");
  } catch (err) {
    console.error("refreshAttendees error:", err);
  }
}

async function removeAttendee(attendanceId) {
  if (!confirm("Are you sure you want to invalidate this attendance check-in?")) return;
  try {
    const res = await fetch(`/api/presenter/${lessonId}/attendees/${attendanceId}`, {
      method: "DELETE",
    });
    if (res.ok) {
      await refreshAttendees();
      await refreshPresenter();
    } else {
      alert("Failed to remove attendance record.");
    }
  } catch (err) {
    alert("Error removing attendance record.");
  }
}

// Initial cycle
refreshPresenter();
refreshAttendees();

// Auto refresh QR every 5s, attendees list every 4s
setInterval(refreshPresenter, 5000);
setInterval(refreshAttendees, 4000);

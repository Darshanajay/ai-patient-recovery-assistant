
import "./App.css";
import { useEffect, useState } from "react";
import axios from "axios";

import {
  LayoutDashboard,
  Pill,
  CalendarDays,
  ClipboardList,
  Activity,
  UserRound,
  Bell,
  HeartPulse,
  Upload,
  CheckCircle2,
  Clock,
  AlertCircle,
  History as HistoryIcon,
  FileText,
  RefreshCw,
  Eye,
  Download,
  ShieldCheck,
} from "lucide-react";

const AI_API = "http://127.0.0.1:8000";
const BACKEND_API = "http://localhost:8080/api/caregiver-tasks";
const HISTORY_API = "http://localhost:8080/api/pdf-history";
const REVIEW_API = "http://localhost:8080/api/professional-reviews";

const PATIENT_ID = 1;
const STORAGE_KEY = "recoveryAnalysis";

// -------------------------------------
// PROFESSIONAL AUTHENTICATION
// -------------------------------------

let professionalCredentials = null;
let credentialPromise = null;

async function getProfessionalCredentials() {
  if (professionalCredentials) {
    return professionalCredentials;
  }

  if (!credentialPromise) {
    credentialPromise = (async () => {
      const username = window.prompt(
        "Enter professional demo account email:",
        "darshudarshan85901@gmail.com"
      );

      if (!username || !username.trim()) {
        throw new Error("Login cancelled.");
      }

      const password = window.prompt("Enter your password:");

      if (!password) {
        throw new Error("Login cancelled.");
      }

      return {
        username: username.trim(),
        password,
      };
    })().finally(() => {
      credentialPromise = null;
    });
  }

  professionalCredentials = await credentialPromise;

  return professionalCredentials;
}

async function backendRequest(config) {
  const credentials = await getProfessionalCredentials();

  try {
    return await axios.request({
      ...config,
      auth: credentials,
    });
  } catch (error) {
    if (error.response?.status === 401) {
      professionalCredentials = null;
    }

    throw error;
  }
}

// -------------------------------------
// MAIN APP
// -------------------------------------

function App() {
  const [active, setActive] = useState("Dashboard");
  const [file, setFile] = useState(null);

  const [result, setResult] = useState(() => {
    try {
      const savedResult = localStorage.getItem(STORAGE_KEY);
      return savedResult ? JSON.parse(savedResult) : null;
    } catch {
      return null;
    }
  });

  const [loading, setLoading] = useState(false);
  const [taskLoading, setTaskLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [reviewLoading, setReviewLoading] = useState(false);

  const [error, setError] = useState("");
  const [taskError, setTaskError] = useState("");
  const [historyError, setHistoryError] = useState("");
  const [reviewError, setReviewError] = useState("");

  const [savedTasks, setSavedTasks] = useState([]);
  const [pdfHistory, setPdfHistory] = useState([]);
  const [pendingReviews, setPendingReviews] = useState([]);
  const [reviewHistory, setReviewHistory] = useState([]);

  const [selectedTask, setSelectedTask] = useState(null);
  const [reviewComments, setReviewComments] = useState("");
  const [reviewMessage, setReviewMessage] = useState("");

  const menu = [
    { name: "Dashboard", icon: LayoutDashboard },
    { name: "Medications", icon: Pill },
    { name: "Appointments", icon: CalendarDays },
    { name: "Recovery Tasks", icon: ClipboardList },
    { name: "Progress", icon: Activity },
    { name: "PDF History", icon: HistoryIcon },
    { name: "Professional Review", icon: ShieldCheck },
  ];

  const pendingConfirmations =
    result?.pending_confirmations || [];

  const completedCount = savedTasks.filter(
    (task) => task.status === "COMPLETED"
  ).length;

  const pendingCount = savedTasks.length - completedCount;

  const reviewCount = savedTasks.filter(
    (task) =>
      !task.verificationStatus ||
      task.verificationStatus === "REQUIRES_REVIEW"
  ).length;

  // -------------------------------------
  // INITIAL DATA
  // -------------------------------------

  useEffect(() => {
    fetchTasks();
    fetchHistory();
  }, []);

  // -------------------------------------
  // FETCH TASKS
  // -------------------------------------

  const fetchTasks = async () => {
    setTaskLoading(true);
    setTaskError("");

    try {
      const response = await backendRequest({
        method: "GET",
        url: `${BACKEND_API}/${PATIENT_ID}`,
      });

      setSavedTasks(response.data);
    } catch (err) {
      console.error("Task loading error:", err);
      setTaskError(
        err.message === "Login cancelled."
          ? "Login cancelled. Please allow the login prompts and refresh."
          : "Unable to load tasks. Check backend login."
      );
    } finally {
      setTaskLoading(false);
    }
  };

  // -------------------------------------
  // FETCH PDF HISTORY
  // -------------------------------------

  const fetchHistory = async () => {
    setHistoryLoading(true);
    setHistoryError("");

    try {
      const response = await backendRequest({
        method: "GET",
        url: `${HISTORY_API}/${PATIENT_ID}`,
      });

      setPdfHistory(response.data);
    } catch (err) {
      console.error("PDF history loading error:", err);
      setHistoryError("Unable to load PDF history.");
    } finally {
      setHistoryLoading(false);
    }
  };

  // -------------------------------------
  // FETCH PROFESSIONAL REVIEWS
  // -------------------------------------

  const fetchPendingReviews = async () => {
    setReviewLoading(true);
    setReviewError("");

    try {
      const response = await backendRequest({
        method: "GET",
        url: `${REVIEW_API}/pending`,
      });

      setPendingReviews(response.data);
    } catch (err) {
      console.error("Pending review error:", err);
      setReviewError(
        "Unable to load professional review tasks."
      );
    } finally {
      setReviewLoading(false);
    }
  };

  const fetchReviewHistory = async (taskId) => {
    try {
      const response = await backendRequest({
        method: "GET",
        url: `${REVIEW_API}/history/${taskId}`,
      });

      setReviewHistory(response.data);
    } catch (err) {
      console.error("Review history error:", err);
      setReviewError("Unable to load review history.");
    }
  };

  // -------------------------------------
  // SUBMIT PROFESSIONAL REVIEW
  // -------------------------------------

  const submitReview = async (decision) => {
    if (!selectedTask) {
      setReviewError("Please select a task.");
      return;
    }

    setReviewError("");
    setReviewMessage("");

    try {
      await backendRequest({
        method: "POST",
        url: `${REVIEW_API}/${selectedTask.id}`,
        data: {
          decision,
          comments: reviewComments,
        },
      });

      setReviewMessage(
        "Review activity recorded successfully."
      );

      setReviewComments("");

      await fetchPendingReviews();
      await fetchReviewHistory(selectedTask.id);
    } catch (err) {
      console.error("Review submission error:", err);
      setReviewError(
        err.response?.data?.message ||
          "Unable to submit review. Check your professional login."
      );
    }
  };

  // -------------------------------------
  // UPLOAD AND ANALYZE PDF
  // -------------------------------------

  const uploadSummary = async () => {
    if (!file) {
      setError("Please select a PDF file first.");
      return;
    }

    if (
      file.type !== "application/pdf" ||
      !file.name.toLowerCase().endsWith(".pdf")
    ) {
      setError("Please select a valid PDF file.");
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setError("PDF file must be below 10 MB.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      // 1. Send PDF to AI service
      const formData = new FormData();
      formData.append("file", file);

      const response = await axios.post(
        `${AI_API}/upload-summary`,
        formData
      );

      const aiResult = response.data;

      // 2. Save analysis
      setResult(aiResult);

      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify(aiResult)
      );

      // 3. Save original PDF in backend
      const historyFormData = new FormData();
      historyFormData.append("file", file);

      await backendRequest({
        method: "POST",
        url: `${HISTORY_API}/upload/${PATIENT_ID}`,
        data: historyFormData,
      });

      await fetchHistory();

      // 4. Get existing tasks
      const existingResponse = await backendRequest({
        method: "GET",
        url: `${BACKEND_API}/${PATIENT_ID}`,
      });

      const existingDescriptions = new Set(
        existingResponse.data.map(
          (task) => task.taskDescription
        )
      );

      // 5. Identify new AI tasks
      const extractedTasks = aiResult.recovery_tasks || [];

      const newTasks = extractedTasks.filter((task) => {
        const description =
          typeof task === "string"
            ? task
            : task.task ||
              task.taskDescription ||
              task.description;

        return (
          description &&
          !existingDescriptions.has(description)
        );
      });

      // 6. Save new tasks
      await Promise.all(
        newTasks.map((task) => {
          const description =
            typeof task === "string"
              ? task
              : task.task ||
                task.taskDescription ||
                task.description;

          return backendRequest({
            method: "POST",
            url: `${BACKEND_API}/${PATIENT_ID}`,
            data: {
              taskDescription: description,
            },
          });
        })
      );

      // 7. Refresh tasks
      await fetchTasks();

      setFile(null);

      const fileInput = document.getElementById("pdf-upload");

      if (fileInput) {
        fileInput.value = "";
      }
    } catch (err) {
      console.error("Upload error:", err);

      setError(
        err.response?.data?.detail ||
          err.response?.data?.message ||
          err.message ||
          "Unable to upload PDF. Check your services and login."
      );
    } finally {
      setLoading(false);
    }
  };

  // -------------------------------------
  // CAREGIVER TASK ACKNOWLEDGEMENT
  // -------------------------------------

  const toggleTask = async (taskId, checked) => {
    setTaskError("");

    const newStatus = checked ? "COMPLETED" : "PENDING";

    try {
      const response = await backendRequest({
        method: "PATCH",
        url: `${BACKEND_API}/${taskId}/status`,
        data: {
          status: newStatus,
        },
      });

      setSavedTasks((previous) =>
        previous.map((task) =>
          task.id === taskId ? response.data : task
        )
      );
    } catch (err) {
      console.error("Status update error:", err);
      setTaskError("Unable to update caregiver status.");
    }
  };

  // -------------------------------------
  // REFRESH
  // -------------------------------------

  const refreshData = async () => {
    await Promise.all([
      fetchTasks(),
      fetchHistory(),
      fetchPendingReviews(),
    ]);
  };

  // -------------------------------------
  // PDF VIEW
  // -------------------------------------

  const viewPdf = async (id) => {
    try {
      const response = await backendRequest({
        method: "GET",
        url: `${HISTORY_API}/view/${id}`,
        responseType: "blob",
      });

      const blobUrl = window.URL.createObjectURL(
        new Blob([response.data], {
          type: "application/pdf",
        })
      );

      window.open(blobUrl, "_blank", "noopener,noreferrer");

      setTimeout(() => {
        window.URL.revokeObjectURL(blobUrl);
      }, 60000);
    } catch (err) {
      console.error("PDF view error:", err);
      setHistoryError("Unable to open this PDF.");
    }
  };

  // -------------------------------------
  // PDF DOWNLOAD
  // -------------------------------------

  const downloadPdf = async (item) => {
    try {
      const response = await backendRequest({
        method: "GET",
        url: `${HISTORY_API}/download/${item.id}`,
        responseType: "blob",
      });

      const blobUrl = window.URL.createObjectURL(
        new Blob([response.data], {
          type: "application/pdf",
        })
      );

      const link = document.createElement("a");

      link.href = blobUrl;
      link.download =
        item.originalFileName || "uploaded-summary.pdf";

      document.body.appendChild(link);
      link.click();
      link.remove();

      window.URL.revokeObjectURL(blobUrl);
    } catch (err) {
      console.error("PDF download error:", err);
      setHistoryError("Unable to download this PDF.");
    }
  };

  // -------------------------------------
  // HELPERS
  // -------------------------------------

  const getConfirmationText = (item) => {
    return typeof item === "string"
      ? item
      : item?.task ||
          item?.description ||
          "Confirmation required";
  };

  const getVerificationLabel = (status) => {
    if (status === "VERIFIED") {
      return "Verified by authorized professional";
    }

    return "Requires professional review";
  };

  const PageHeader = ({ title, description }) => (
    <div style={{ marginBottom: 24 }}>
      <h2>{title}</h2>
      <p>{description}</p>
    </div>
  );

  const EmptyState = ({ message }) => (
    <div style={{ padding: "18px 0" }}>
      <AlertCircle size={25} color="#087f70" />
      <p>{message}</p>
    </div>
  );

  // -------------------------------------
  // CAREGIVER TASK LIST
  // -------------------------------------

  const TaskList = () => (
    <div>
      {taskLoading ? (
        <p>Loading tasks from database...</p>
      ) : savedTasks.length === 0 ? (
        <EmptyState message="No recovery tasks available yet. Upload a fictional demonstration discharge summary." />
      ) : (
        savedTasks.map((task) => (
          <div
            key={task.id}
            className="card"
            style={{ marginBottom: 18, padding: 16 }}
          >
            <label
              style={{
                display: "flex",
                gap: 12,
                alignItems: "flex-start",
                cursor: "pointer",
              }}
            >
              <input
                type="checkbox"
                checked={task.status === "COMPLETED"}
                onChange={(event) =>
                  toggleTask(task.id, event.target.checked)
                }
              />

              <span>{task.taskDescription}</span>
            </label>

            <p style={{ marginLeft: 29 }}>
              Caregiver status:{" "}
              {task.status === "COMPLETED"
                ? "Acknowledged by caregiver"
                : "Pending acknowledgement"}
            </p>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                marginLeft: 29,
                marginTop: 8,
              }}
            >
              <ShieldCheck size={18} color="#b7791f" />

              <span>
                Professional verification:{" "}
                <strong>
                  {getVerificationLabel(
                    task.verificationStatus
                  )}
                </strong>
              </span>
            </div>
          </div>
        ))
      )}

      {taskError && (
        <p style={{ color: "red" }}>{taskError}</p>
      )}
    </div>
  );

  // -------------------------------------
  // PDF HISTORY LIST
  // -------------------------------------

  const HistoryList = () => (
    <div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 20,
          flexWrap: "wrap",
          gap: 12,
        }}
      >
        <p>Previously uploaded demonstration PDFs</p>

        <button onClick={refreshData}>
          <RefreshCw size={16} />
          Refresh
        </button>
      </div>

      {historyLoading ? (
        <p>Loading PDF history...</p>
      ) : pdfHistory.length === 0 ? (
        <EmptyState message="No PDF upload history found." />
      ) : (
        pdfHistory.map((item) => (
          <div
            key={item.id}
            className="card"
            style={{ marginBottom: 16 }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 12,
              }}
            >
              <FileText size={28} color="#087f70" />

              <div>
                <h3>
                  {item.originalFileName || "Uploaded PDF"}
                </h3>

                <p>
                  Uploaded:{" "}
                  {item.uploadedAt
                    ? new Date(item.uploadedAt).toLocaleString()
                    : "Not available"}
                </p>

                <p>
                  Analysis status:{" "}
                  {item.analysisStatus || "Not available"}
                </p>
              </div>
            </div>

            <div
              style={{
                display: "flex",
                gap: 10,
                marginTop: 16,
                flexWrap: "wrap",
              }}
            >
              <button onClick={() => viewPdf(item.id)}>
                <Eye size={16} />
                View PDF
              </button>

              <button onClick={() => downloadPdf(item)}>
                <Download size={16} />
                Download PDF
              </button>
            </div>
          </div>
        ))
      )}

      {historyError && (
        <p style={{ color: "red" }}>{historyError}</p>
      )}
    </div>
  );

  // -------------------------------------
  // PROFESSIONAL REVIEW PAGE
  // -------------------------------------

  const ProfessionalReviewPage = () => (
    <section className="panel">
      <PageHeader
        title="Professional Review"
        description="Review extracted demonstration tasks and record review activity."
      />

      <div
        style={{
          display: "flex",
          gap: 12,
          flexWrap: "wrap",
          marginBottom: 20,
        }}
      >
        <button onClick={fetchPendingReviews}>
          <RefreshCw size={16} />
          Refresh Pending Reviews
        </button>
      </div>

      {reviewLoading ? (
        <p>Loading professional review tasks...</p>
      ) : pendingReviews.length === 0 ? (
        <EmptyState message="No tasks are currently awaiting review." />
      ) : (
        pendingReviews.map((task) => (
          <div
            key={task.id}
            className="card"
            style={{
              marginBottom: 16,
              padding: 18,
              border:
                selectedTask?.id === task.id
                  ? "2px solid #087f70"
                  : undefined,
            }}
          >
            <h3>{task.taskDescription}</h3>

            <p>
              Task ID: {task.id}
            </p>

            <p>
              Caregiver status: {task.status}
            </p>

            <p>
              Verification status:{" "}
              {task.verificationStatus || "REQUIRES_REVIEW"}
            </p>

            <button
              onClick={() => {
                setSelectedTask(task);
                setReviewMessage("");
                setReviewError("");
                fetchReviewHistory(task.id);
              }}
            >
              <Eye size={16} />
              Select for Review
            </button>
          </div>
        ))
      )}

      {selectedTask && (
        <div
          className="card"
          style={{ padding: 20, marginTop: 24 }}
        >
          <h3>Selected Task</h3>

          <p>{selectedTask.taskDescription}</p>

          <label>
            Review comments
          </label>

          <textarea
            value={reviewComments}
            onChange={(event) =>
              setReviewComments(event.target.value)
            }
            placeholder="Enter demonstration review comments..."
            rows={4}
            style={{
              width: "100%",
              padding: 12,
              marginTop: 10,
              marginBottom: 16,
              boxSizing: "border-box",
            }}
          />

          <div
            style={{
              display: "flex",
              gap: 10,
              flexWrap: "wrap",
            }}
          >
            <button
              onClick={() => submitReview("REVIEWED")}
            >
              <CheckCircle2 size={16} />
              Record Reviewed
            </button>

            <button
              onClick={() =>
                submitReview("NEEDS_CLARIFICATION")
              }
            >
              <AlertCircle size={16} />
              Needs Clarification
            </button>
          </div>

          {reviewMessage && (
            <p style={{ color: "green" }}>
              {reviewMessage}
            </p>
          )}

          <h4>Review History</h4>

          {reviewHistory.length === 0 ? (
            <p>No review activity recorded yet.</p>
          ) : (
            reviewHistory.map((review) => (
              <div
                key={review.reviewId}
                className="card"
                style={{ padding: 14, marginBottom: 12 }}
              >
                <p>
                  Decision: <strong>{review.decision}</strong>
                </p>

                <p>
                  Reviewer: {review.professionalName}
                </p>

                <p>
                  Comments: {review.comments || "None"}
                </p>

                <small>
                  {review.reviewedAt
                    ? new Date(
                        review.reviewedAt
                      ).toLocaleString()
                    : ""}
                </small>
              </div>
            ))
          )}
        </div>
      )}

      {reviewError && (
        <p style={{ color: "red" }}>{reviewError}</p>
      )}

      <p style={{ marginTop: 20 }}>
        Demo review activity is recorded for audit purposes.
        It does not automatically verify clinical instructions
        or change a task's medical verification status.
        Clinical decisions require an authorized healthcare
        professional.
      </p>
    </section>
  );

  // -------------------------------------
  // MAIN UI
  // -------------------------------------

  return (
    <div className="app">
      {/* SIDEBAR */}

      <aside className="sidebar">
        <h2>
          <HeartPulse /> RecoveryAI
        </h2>

        <p className="menu-title">MENU</p>

        {menu.map((item) => {
          const Icon = item.icon;

          return (
            <button
              key={item.name}
              className={active === item.name ? "active" : ""}
              onClick={() => {
                setActive(item.name);

                if (item.name === "Professional Review") {
                  fetchPendingReviews();
                }
              }}
            >
              <Icon size={19} />
              {item.name}
            </button>
          );
        })}

        <div className="profile">
          <UserRound />

          <div>
            <strong>Rahul Sharma</strong>
            <small>Demo Caregiver</small>
          </div>
        </div>
      </aside>

      {/* MAIN CONTENT */}

      <main className="main">
        <header>
          <div>
            <h1>{active}</h1>
            <p>Your personal recovery companion</p>
          </div>

          <Bell />
        </header>

        {/* DASHBOARD */}

        {active === "Dashboard" && (
          <>
            <section className="welcome">
              <h2>Welcome back, Darshan!</h2>
              <p>
                Let's make today another step towards recovery.
              </p>
            </section>

            <section className="cards">
              <div className="card">
                <Activity />
                <h3>Recovery Tasks</h3>
                <h2>{savedTasks.length}</h2>
                <p>Tasks stored in database</p>
              </div>

              <div className="card">
                <CheckCircle2 />
                <h3>Caregiver Acknowledgements</h3>
                <h2>{completedCount}</h2>
                <p>Tasks marked by caregiver</p>
              </div>

              <div className="card">
                <ShieldCheck />
                <h3>Awaiting Professional Review</h3>
                <h2>{reviewCount}</h2>
                <p>Tasks requiring review</p>
              </div>
            </section>

            <section className="details">
              <div className="panel">
                <h3>
                  <ClipboardList size={19} />
                  Today's Recovery Tasks
                </h3>

                <TaskList />

                <p>
                  Caregiver acknowledgement does not medically
                  verify a task or its clinical instructions.
                </p>
              </div>

              <div className="panel">
                <h3>
                  <Upload size={19} />
                  AI Recovery Assistant
                </h3>

                <p>
                  Upload a fictional demonstration discharge
                  summary PDF.
                </p>

                <input
                  id="pdf-upload"
                  type="file"
                  accept=".pdf,application/pdf"
                  onChange={(event) => {
                    setFile(event.target.files[0] || null);
                    setError("");
                  }}
                />

                {file && <p>Selected: {file.name}</p>}

                <button
                  onClick={uploadSummary}
                  disabled={loading}
                >
                  {loading
                    ? "Analyzing and saving..."
                    : "Upload and Analyze"}
                </button>

                {error && (
                  <p style={{ color: "red" }}>{error}</p>
                )}

                {result && (
                  <>
                    <h4>Previous AI Analysis (Demo)</h4>

                    <p>
                      Name:{" "}
                      {result.patient_details?.patient_name ||
                        "Not available"}
                    </p>

                    <p>
                      Age:{" "}
                      {result.patient_details?.age ??
                        "Not available"}
                    </p>

                    <p>
                      Discharge Date:{" "}
                      {result.patient_details?.discharge_date ||
                        "Not available"}
                    </p>

                    <h4>Safety Notes</h4>

                    {(result.safety_notes || []).map(
                      (note, index) => (
                        <p key={index}>{note}</p>
                      )
                    )}

                    <h4>Analysis Status</h4>
                    <p>{result.status}</p>
                  </>
                )}
              </div>
            </section>
          </>
        )}

        {/* MEDICATIONS */}

        {active === "Medications" && (
          <section className="panel">
            <PageHeader
              title="Medication Information"
              description="Review medication information documented in the discharge summary."
            />

            <EmptyState message="No verified medication list is available. Confirm medication information with the treating healthcare professional." />

            {pendingConfirmations.map((item, index) => (
              <p key={index}>
                {getConfirmationText(item)}
              </p>
            ))}

            <p>
              The application does not generate or modify
              medication instructions.
            </p>
          </section>
        )}

        {/* APPOINTMENTS */}

        {active === "Appointments" && (
          <section className="panel">
            <PageHeader
              title="Follow-up Appointments"
              description="Review appointment information and outstanding confirmations."
            />

            {pendingConfirmations.length === 0 ? (
              <EmptyState message="No appointment confirmation information is available." />
            ) : (
              pendingConfirmations.map((item, index) => (
                <div
                  key={index}
                  style={{ marginBottom: 18 }}
                >
                  <CalendarDays color="#087f70" />
                  <p>{getConfirmationText(item)}</p>
                  <small>Status: Requires confirmation</small>
                </div>
              ))
            )}

            <p>
              Confirm appointment details directly with the
              hospital.
            </p>
          </section>
        )}

        {/* RECOVERY TASKS */}

        {active === "Recovery Tasks" && (
          <section className="panel">
            <PageHeader
              title="Recovery Task Management"
              description="Track documented tasks, caregiver acknowledgements and professional review status."
            />

            <TaskList />

            <h4>Pending Confirmations</h4>

            {pendingConfirmations.length === 0 ? (
              <p>No pending confirmations returned.</p>
            ) : (
              pendingConfirmations.map((item, index) => (
                <div
                  key={index}
                  style={{ marginBottom: 15 }}
                >
                  <p>{getConfirmationText(item)}</p>
                  <small>Status: Requires confirmation</small>
                </div>
              ))
            )}

            <p>
              Clinical instructions must be reviewed by an
              authorized healthcare professional before use.
            </p>
          </section>
        )}

        {/* PROGRESS */}

        {active === "Progress" && (
          <section className="panel">
            <PageHeader
              title="Caregiver Tracking"
              description="View caregiver acknowledgement statistics."
            />

            <div className="cards">
              <div className="card">
                <ClipboardList />
                <h3>Total Tasks</h3>
                <h2>{savedTasks.length}</h2>
              </div>

              <div className="card">
                <CheckCircle2 />
                <h3>Acknowledged</h3>
                <h2>{completedCount}</h2>
              </div>

              <div className="card">
                <Clock />
                <h3>Not Acknowledged</h3>
                <h2>{pendingCount}</h2>
              </div>
            </div>

            {savedTasks.length > 0 && (
              <>
                <h4>Caregiver Acknowledgement Progress</h4>

                <progress
                  value={completedCount}
                  max={savedTasks.length}
                  style={{ width: "100%", height: 12 }}
                />

                <p>
                  {Math.round(
                    (completedCount / savedTasks.length) * 100
                  )}
                  % acknowledged
                </p>
              </>
            )}

            <p>
              This is a caregiver tracking indicator, not a
              measure of the patient's medical recovery.
            </p>
          </section>
        )}

        {/* PDF HISTORY */}

        {active === "PDF History" && (
          <section className="panel">
            <PageHeader
              title="PDF Upload History"
              description="View previously uploaded demonstration discharge summaries."
            />

            <HistoryList />
          </section>
        )}

        {/* PROFESSIONAL REVIEW */}

        {active === "Professional Review" && (
          <ProfessionalReviewPage />
        )}
      </main>
    </div>
  );
}

export default App;

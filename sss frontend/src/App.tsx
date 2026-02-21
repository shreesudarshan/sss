/*
  Frontend application shell.

  This file provides:
  - Register/login/logout flow
  - Authenticated patient creation
  - Authenticated patient search
  - Basic API request handling with cookie sessions
*/

import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import "./App.css";

const ENV_API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").trim();
const ENV_API_PORT = (import.meta.env.VITE_API_PORT ?? "").trim();

function resolveApiBaseUrl(): string {
  if (ENV_API_BASE_URL) {
    return ENV_API_BASE_URL.replace(/\/+$/, "");
  }

  if (typeof window === "undefined") {
    return "http://localhost:8000";
  }

  const { protocol, hostname, port } = window.location;
  const isLocalHost = hostname === "localhost" || hostname === "127.0.0.1";
  const resolvedPort = ENV_API_PORT || (isLocalHost ? "8000" : port);
  const hostWithPort = resolvedPort ? `${hostname}:${resolvedPort}` : hostname;
  return `${protocol}//${hostWithPort}`;
}

const API_BASE_URL = resolveApiBaseUrl();

type User = {
  id: number;
  email: string;
};

type Patient = {
  id: number;
  name: string;
  dob: string;
  diagnosis: string;
};

type AuthMode = "login" | "register";

async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  // Shared API wrapper used by auth and patient actions.
  const response = await fetch(`${API_BASE_URL}${path}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  const raw = await response.text();
  let payload: unknown = {};
  if (raw) {
    try {
      payload = JSON.parse(raw);
    } catch {
      payload = { detail: raw };
    }
  }

  if (!response.ok) {
    const detail =
      typeof payload === "object" && payload !== null && "detail" in payload
        ? String((payload as { detail: unknown }).detail)
        : `Request failed with status ${response.status}`;
    throw new Error(detail);
  }

  return payload as T;
}

function App() {
  // Authentication state.
  const [authMode, setAuthMode] = useState<AuthMode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [user, setUser] = useState<User | null>(null);
  const [authError, setAuthError] = useState("");
  const [authBusy, setAuthBusy] = useState(false);

  // Patient form and search state.
  const [name, setName] = useState("");
  const [dob, setDob] = useState("");
  const [diagnosis, setDiagnosis] = useState("");
  const [patientBusy, setPatientBusy] = useState(false);
  const [patientMessage, setPatientMessage] = useState("");

  const [searchQuery, setSearchQuery] = useState("");
  const [searchBusy, setSearchBusy] = useState(false);
  const [searchResults, setSearchResults] = useState<Patient[]>([]);

  useEffect(() => {
    // On first render, attempt to restore the existing login session.
    const bootstrap = async () => {
      try {
        const me = await apiRequest<User>("/auth/me");
        setUser(me);
      } catch {
        setUser(null);
      }
    };
    void bootstrap();
  }, []);

  const submitAuth = async (event: FormEvent) => {
    // Register (optional) then login.
    event.preventDefault();
    setAuthError("");
    setAuthBusy(true);
    try {
      if (authMode === "register") {
        await apiRequest<User>("/auth/register", {
          method: "POST",
          body: JSON.stringify({ email, password }),
        });
      }
      const me = await apiRequest<User>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      setUser(me);
    } catch (error) {
      setAuthError(error instanceof Error ? error.message : "Authentication failed");
    } finally {
      setAuthBusy(false);
    }
  };

  const logout = async () => {
    // Revoke server session and reset local state.
    try {
      await apiRequest<{ status: string }>("/auth/logout", { method: "POST" });
    } finally {
      setUser(null);
      setSearchResults([]);
      setPatientMessage("");
    }
  };

  const createPatient = async (event: FormEvent) => {
    // Send patient payload to encrypted backend create endpoint.
    event.preventDefault();
    setPatientBusy(true);
    setPatientMessage("");
    try {
      const created = await apiRequest<{ patient_id: number }>("/patients/", {
        method: "POST",
        body: JSON.stringify({ name, dob, diagnosis }),
      });
      setPatientMessage(`Patient created with ID ${created.patient_id}`);
      setName("");
      setDob("");
      setDiagnosis("");
    } catch (error) {
      setPatientMessage(error instanceof Error ? error.message : "Failed to create patient");
    } finally {
      setPatientBusy(false);
    }
  };

  const searchPatients = async (event: FormEvent) => {
    // Query backend blind-index search endpoint.
    event.preventDefault();
    setSearchBusy(true);
    try {
      const patients = await apiRequest<Patient[]>(
        `/patients/search?query=${encodeURIComponent(searchQuery)}`
      );
      setSearchResults(patients);
    } catch {
      setSearchResults([]);
    } finally {
      setSearchBusy(false);
    }
  };

  if (!user) {
    return (
      <main className="page">
        <section className="panel auth-panel">
          <h1>Secure Bloom SSE</h1>
          <p className="subtitle">Basic Auth + Encrypted Patients</p>
          <div className="tabs">
            <button
              className={authMode === "login" ? "tab active" : "tab"}
              onClick={() => setAuthMode("login")}
              type="button"
            >
              Login
            </button>
            <button
              className={authMode === "register" ? "tab active" : "tab"}
              onClick={() => setAuthMode("register")}
              type="button"
            >
              Register
            </button>
          </div>
          <form onSubmit={submitAuth} className="form">
            <label>
              Email
              <input
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                type="email"
                required
              />
            </label>
            <label>
              Password
              <input
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                type="password"
                minLength={8}
                required
              />
            </label>
            {authError ? <p className="error">{authError}</p> : null}
            <button type="submit" className="primary" disabled={authBusy}>
              {authBusy ? "Working..." : authMode === "login" ? "Login" : "Register + Login"}
            </button>
          </form>
        </section>
      </main>
    );
  }

  return (
    <main className="page">
      <header className="panel header-panel">
        <div>
          <h1>Secure Bloom SSE</h1>
          <p className="subtitle">Signed in as {user.email}</p>
        </div>
        <button onClick={logout} className="danger" type="button">
          Logout
        </button>
      </header>

      <section className="grid">
        <article className="panel">
          <h2>Create Patient</h2>
          <form onSubmit={createPatient} className="form">
            <label>
              Name
              <input value={name} onChange={(event) => setName(event.target.value)} required />
            </label>
            <label>
              DOB
              <input
                value={dob}
                onChange={(event) => setDob(event.target.value)}
                placeholder="YYYY-MM-DD"
                required
              />
            </label>
            <label>
              Diagnosis
              <input
                value={diagnosis}
                onChange={(event) => setDiagnosis(event.target.value)}
                required
              />
            </label>
            <button type="submit" className="primary" disabled={patientBusy}>
              {patientBusy ? "Saving..." : "Create Patient"}
            </button>
          </form>
          {patientMessage ? <p className="status">{patientMessage}</p> : null}
        </article>

        <article className="panel">
          <h2>Search Patients</h2>
          <form onSubmit={searchPatients} className="inline-form">
            <input
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="name or diagnosis"
              required
            />
            <button type="submit" className="primary" disabled={searchBusy}>
              {searchBusy ? "Searching..." : "Search"}
            </button>
          </form>
          <ul className="results">
            {searchResults.map((patient) => (
              <li key={patient.id}>
                <strong>{patient.name}</strong>
                <span>{patient.dob}</span>
                <span>{patient.diagnosis}</span>
                <span>ID {patient.id}</span>
              </li>
            ))}
          </ul>
          {!searchResults.length ? <p className="subtitle">No search results yet.</p> : null}
        </article>
      </section>
    </main>
  );
}

export default App;

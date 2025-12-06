const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiClient {
  private token: string | null = null;

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem("token", token);
    } else {
      localStorage.removeItem("token");
    }
  }

  getToken(): string | null {
    if (this.token) return this.token;
    if (typeof window !== "undefined") {
      this.token = localStorage.getItem("token");
    }
    return this.token;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = this.getToken();
    const headers: HeadersInit = {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    };

    if (token) {
      (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || "Request failed");
    }

    return response.json();
  }

  // Auth
  async register(email: string, password: string, fullName: string, phone?: string) {
    return this.request<{ access_token: string; caregiver: any }>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({
        email,
        password,
        full_name: fullName,
        phone_number: phone,
      }),
    });
  }

  async login(email: string, password: string) {
    return this.request<{ access_token: string; caregiver: any }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  }

  // Patients
  async getPatients() {
    return this.request<any[]>("/api/patients");
  }

  async getPatient(id: string) {
    return this.request<any>(`/api/patients/${id}`);
  }

  async createPatient(data: {
    full_name: string;
    phone_number: string;
    date_of_birth?: string;
  }) {
    return this.request<any>("/api/patients", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updatePatient(id: string, data: any) {
    return this.request<any>(`/api/patients/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deletePatient(id: string) {
    return this.request<any>(`/api/patients/${id}`, {
      method: "DELETE",
    });
  }

  async triggerCall(patientId: string, sessionType: string = "onboarding") {
    return this.request<any>(`/api/patients/${patientId}/trigger-call?session_type=${sessionType}`, {
      method: "POST",
    });
  }

  async getAdherenceStats(patientId: string, days = 30) {
    return this.request<any>(`/api/patients/${patientId}/adherence-stats?days=${days}`);
  }

  // Medications
  async getPatientMedications(patientId: string) {
    return this.request<any[]>(`/api/patients/${patientId}/medications`);
  }

  async createMedication(patientId: string, data: any) {
    return this.request<any>(`/api/patients/${patientId}/medications`, {
      method: "POST",
      body: JSON.stringify({ ...data, patient_id: patientId }),
    });
  }

  async updateMedication(id: string, data: any) {
    return this.request<any>(`/api/medications/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteMedication(id: string) {
    return this.request<any>(`/api/medications/${id}`, {
      method: "DELETE",
    });
  }

  async searchDrugs(query: string) {
    return this.request<any[]>(`/api/medications/search?query=${encodeURIComponent(query)}`, {
      method: "POST",
    });
  }

  // Reminders
  async getTodayReminders() {
    return this.request<any[]>("/api/reminders/today");
  }

  async getUpcomingReminders(days = 7) {
    return this.request<any[]>(`/api/reminders/upcoming?days=${days}`);
  }

  async markReminderTaken(id: string) {
    return this.request<any>(`/api/reminders/${id}/mark-taken`, {
      method: "POST",
    });
  }

  // Voice Sessions (replaces Calls)
  async getVoiceSessions(limit = 50) {
    return this.request<any[]>(`/api/voice/sessions?limit=${limit}`);
  }

  async getVoiceSession(id: string) {
    return this.request<any>(`/api/voice/sessions/${id}`);
  }

  async triggerVoiceCall(patientId: string, sessionType: string, metadata?: any) {
    return this.request<any>(`/api/voice/trigger-call/${patientId}`, {
      method: "POST",
      body: JSON.stringify({
        session_type: sessionType,
        metadata: metadata || {}
      }),
    });
  }

  // Chat
  async sendChatMessage(patientId: string, messages: { role: string; content: string }[]) {
    return this.request<{
      message: string;
      medication_data?: any;
      medication_saved: boolean;
    }>("/api/chat/prescription", {
      method: "POST",
      body: JSON.stringify({ patient_id: patientId, messages }),
    });
  }
}

export const api = new ApiClient();

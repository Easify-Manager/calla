import { create } from "zustand";
import { api } from "./api";

interface Caregiver {
  id: string;
  email: string;
  full_name: string;
  phone_number?: string;
  created_at: string;
}

interface AuthState {
  caregiver: Caregiver | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string, phone?: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  caregiver: null,
  isLoading: true,
  isAuthenticated: false,

  login: async (email: string, password: string) => {
    const result = await api.login(email, password);
    api.setToken(result.access_token);
    set({
      caregiver: result.caregiver,
      isAuthenticated: true,
    });
  },

  register: async (email: string, password: string, fullName: string, phone?: string) => {
    const result = await api.register(email, password, fullName, phone);
    api.setToken(result.access_token);
    set({
      caregiver: result.caregiver,
      isAuthenticated: true,
    });
  },

  logout: () => {
    api.setToken(null);
    set({
      caregiver: null,
      isAuthenticated: false,
    });
  },

  checkAuth: () => {
    const token = api.getToken();
    if (token) {
      set({ isAuthenticated: true, isLoading: false });
    } else {
      set({ isLoading: false });
    }
  },
}));

interface Patient {
  id: string;
  full_name: string;
  phone_number: string;
  date_of_birth?: string;
  wake_time?: string;
  breakfast_time?: string;
  lunch_time?: string;
  dinner_time?: string;
  sleep_time?: string;
  onboarding_completed: boolean;
  has_device?: boolean;
  created_at: string;
}

interface PatientState {
  patients: Patient[];
  selectedPatient: Patient | null;
  isLoading: boolean;
  fetchPatients: () => Promise<void>;
  selectPatient: (patient: Patient | null) => void;
  addPatient: (data: { full_name: string; phone_number: string }) => Promise<Patient>;
  removePatient: (id: string) => Promise<void>;
}

export const usePatientStore = create<PatientState>((set, get) => ({
  patients: [],
  selectedPatient: null,
  isLoading: false,

  fetchPatients: async () => {
    set({ isLoading: true });
    try {
      const patients = await api.getPatients();
      set({ patients, isLoading: false });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  selectPatient: (patient) => {
    set({ selectedPatient: patient });
  },

  addPatient: async (data) => {
    const patient = await api.createPatient(data);
    set((state) => ({ patients: [patient, ...state.patients] }));
    return patient;
  },

  removePatient: async (id) => {
    await api.deletePatient(id);
    set((state) => ({
      patients: state.patients.filter((p) => p.id !== id),
      selectedPatient: state.selectedPatient?.id === id ? null : state.selectedPatient,
    }));
  },
}));


import { create } from "zustand";

export interface OnboardingData {
  completed: boolean;
  completed_at?: string;
  preferences?: {
    country?: string;
    profession?: string;
    response_style?: string;
    custom_instructions?: string;
  };
}

export interface UserState {
  profilePicture: string;
  name: string;
  email: string;
  timezone?: string;
  onboarding?: OnboardingData;
}

interface UserStore extends UserState {
  setUser: (user: UserState) => void;
  updateUser: (user: Partial<UserState>) => void;
  clearUser: () => void;
}

const initialState: UserState = {
  profilePicture: "",
  name: "",
  email: "",
  timezone: undefined,
  onboarding: undefined,
};

export const useUserStore = create<UserStore>((set) => ({
  ...initialState,
  setUser: (user: UserState) => set(user),
  updateUser: (user: Partial<UserState>) =>
    set((state) => ({ ...state, ...user })),
  clearUser: () => set(initialState),
}));

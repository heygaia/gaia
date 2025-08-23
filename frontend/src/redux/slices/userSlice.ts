// src/store/userSlice.ts
import { createSlice, PayloadAction } from "@reduxjs/toolkit";

export interface OnboardingData {
  completed: boolean;
  completed_at?: string;
  preferences?: {
    country?: string;
    profession?: string;
    response_style?: string;
    custom_instructions?: string;
    timezone?: string;
  };
}

export interface UserState {
  profilePicture: string;
  name: string;
  email: string;
  onboarding?: OnboardingData;
}

const initialState: UserState = {
  profilePicture: "",
  name: "",
  email: "",
  onboarding: undefined,
};

const userSlice = createSlice({
  name: "user",
  initialState,
  reducers: {
    // Sets user information
    setUser(state, action: PayloadAction<UserState>) {
      state.profilePicture = action.payload.profilePicture;
      state.name = action.payload.name;
      state.email = action.payload.email;
      state.onboarding = action.payload.onboarding;
    },
    // Updates user information partially (preserves existing onboarding state)
    updateUser(state, action: PayloadAction<Partial<UserState>>) {
      if (action.payload.profilePicture !== undefined) {
        state.profilePicture = action.payload.profilePicture;
      }
      if (action.payload.name !== undefined) {
        state.name = action.payload.name;
      }
      if (action.payload.email !== undefined) {
        state.email = action.payload.email;
      }
      if (action.payload.onboarding !== undefined) {
        state.onboarding = action.payload.onboarding;
      }
    },
    // Clears user information
    clearUser(state) {
      state.profilePicture = "";
      state.name = "";
      state.email = "";
      state.onboarding = undefined;
    },
  },
});

export const { setUser, updateUser, clearUser } = userSlice.actions;
export default userSlice.reducer;

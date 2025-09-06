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
  };
}

export interface UserState {
  profilePicture: string;
  name: string;
  email: string;
  onboarding?: OnboardingData;
  selected_model?: string;
}

const initialState: UserState = {
  profilePicture: "",
  name: "",
  email: "",
  onboarding: undefined,
  selected_model: undefined,
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
      state.selected_model = action.payload.selected_model;
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
      state.selected_model = undefined;
    },
  },
});

export const { setUser, updateUser, clearUser } = userSlice.actions;
export default userSlice.reducer;

import { useUserStore } from "@/stores/userStore";

export const useUser = () => {
  const user = useUserStore((state) => ({
    profilePicture: state.profilePicture,
    name: state.name,
    email: state.email,
    timezone: state.timezone,
    onboarding: state.onboarding,
  }));
  return user;
};

export const useUserActions = () => {
  const { setUser, updateUser, clearUser } = useUserStore();
  return { setUser, updateUser, clearUser };
};

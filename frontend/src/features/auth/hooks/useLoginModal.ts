import { useLoginModalStore } from "@/stores/loginModalStore";

export const useLoginModal = () => {
  return useLoginModalStore((state) => state.open);
};

export const useLoginModalActions = () => {
  const setLoginModalOpen = useLoginModalStore(
    (state) => state.setLoginModalOpen,
  );
  return { setLoginModalOpen };
};

"use client";

import { Button } from "@heroui/button";
import { Modal, ModalBody, ModalContent, ModalHeader } from "@heroui/modal";
import { useRouter } from "next/navigation";
import { useDispatch } from "react-redux";
import { toast } from "sonner";

import { authApi } from "@/features/auth/api/authApi";
import { useUserActions } from "@/features/auth/hooks/useUser";
import { chatApi } from "@/features/chat/api/chatApi";
import { useConversation } from "@/features/chat/hooks/useConversation";
import { useFetchConversations } from "@/features/chat/hooks/useConversationList";
import { clearConversations } from "@/redux/slices/conversationsSlice";

import { ModalAction } from "./SettingsMenu";

interface LogoutModalProps {
  modalAction: ModalAction | null;
  setModalAction: (action: ModalAction | null) => void;
}

export default function LogoutModal({
  modalAction,
  setModalAction,
}: LogoutModalProps) {
  const { clearUser } = useUserActions();
  const router = useRouter();
  const dispatch = useDispatch();
  const fetchConversations = useFetchConversations();
  const { updateConvoMessages } = useConversation();

  // Confirm logout action.
  const handleConfirmLogout = async () => {
    try {
      await authApi.logout();
      clearUser();
    } catch (error) {
      console.error("Error during logout:", error);
    } finally {
      setModalAction(null);
      router.push("/login");
    }
  };

  // Confirm clear chats action.
  const handleConfirmClearChats = async () => {
    try {
      router.push("/c");

      await chatApi.deleteAllConversations();

      // Clear conversations in Redux state immediately
      dispatch(clearConversations());

      // Then fetch from the API to ensure sync with server
      await fetchConversations(1, 20, false);

      updateConvoMessages([]);
      // Toast is already shown by the API service
    } catch (error) {
      // Error toast is already shown by the API service
      console.error("Error clearing chats:", error);
    } finally {
      setModalAction(null);
    }
  };

  return (
    <Modal
      isOpen={modalAction !== null}
      backdrop="blur"
      onOpenChange={() => setModalAction(null)}
    >
      <ModalContent>
        <>
          <ModalHeader className="flex justify-center">
            {modalAction === "logout"
              ? "Are you sure you want to logout?"
              : "Are you sure you want to delete all chats?"}
          </ModalHeader>
          <ModalBody className="mb-4 flex flex-col gap-2">
            <Button
              color="danger"
              variant="solid"
              radius="full"
              onPress={() => {
                if (modalAction === "logout") {
                  handleConfirmLogout();
                } else if (modalAction === "clear_chats") {
                  handleConfirmClearChats();
                }
              }}
            >
              {modalAction === "logout" ? "Logout" : "Delete all chats"}
            </Button>
            <Button
              radius="full"
              variant="bordered"
              onPress={() => setModalAction(null)}
            >
              Cancel
            </Button>
          </ModalBody>
        </>
      </ModalContent>
    </Modal>
  );
}

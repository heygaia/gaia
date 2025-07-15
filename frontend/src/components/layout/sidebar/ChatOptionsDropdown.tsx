"use client";

import { Button } from "@heroui/button";
import {
  Dropdown,
  DropdownItem,
  DropdownMenu,
  DropdownTrigger,
} from "@heroui/dropdown";
import { Input } from "@heroui/input";
import {
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
} from "@heroui/modal";
import { DotsVerticalIcon } from "@radix-ui/react-icons";
import { ChevronDown, Star, Trash } from "lucide-react";
import { useRouter } from "next/navigation";
import { ReactNode, SetStateAction, useState } from "react";
import { toast } from "sonner";

import { PencilRenameIcon } from "@/components/shared/icons";
import { chatApi } from "@/features/chat/api/chatApi";
import { useConversation } from "@/features/chat/hooks/useConversation";
import { useFetchConversations } from "@/features/chat/hooks/useConversationList";

export default function ChatOptionsDropdown({
  buttonHovered,
  chatId,
  chatName,
  starred = false,
  logo2 = false,
  btnChildren = undefined,
}: {
  buttonHovered: boolean;
  chatId: string;
  chatName: string;
  starred: boolean | undefined;
  logo2?: boolean;
  btnChildren?: ReactNode;
}) {
  const fetchConversations = useFetchConversations();
  const [dangerStateHovered, setDangerStateHovered] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const { clearMessages } = useConversation();
  const [newName, setNewName] = useState(chatName);
  const router = useRouter();
  const [modalAction, setModalAction] = useState<"edit" | "delete" | null>(
    null,
  );

  const handleStarToggle = async () => {
    try {
      await chatApi.toggleStarConversation(
        chatId,
        starred === undefined ? true : !starred,
      );
      setIsOpen(false);
      toast.success(
        starred === undefined
          ? "Conversation added to starred"
          : starred
            ? "Conversation removed from starred"
            : "Conversation added to starred",
      );

      await fetchConversations();
    } catch (error) {
      toast.error("Could not rename conversation ");

      console.error("Failed to update star", error);
    }
  };

  const handleEdit = async () => {
    if (!newName) return;
    try {
      await chatApi.renameConversation(chatId, newName);
      setIsOpen(false);
      toast.success("Successfully renamed conversation");
      await fetchConversations(1, 20, false);
    } catch (error) {
      toast.error("Could not rename conversation ");
      console.error("Failed to update chat name", error);
    }
  };

  const handleDelete = async () => {
    try {
      router.push("/c");
      clearMessages();
      await chatApi.deleteConversation(chatId);
      setIsOpen(false);
      // Toast is already shown by the API service
      await fetchConversations(1, 20, false);
    } catch (error) {
      // Error toast is already shown by the API service
      console.error("Failed to delete chat", error);
    }
  };

  const openModal = (action: "edit" | "delete") => {
    setModalAction(action);
    setIsOpen(true);
  };

  return (
    <>
      <Dropdown className="w-fit min-w-fit text-foreground dark" size="sm">
        <DropdownTrigger>
          <Button
            className="ml-auto"
            isIconOnly={btnChildren ? false : true}
            variant={btnChildren ? "flat" : "light"}
            radius={btnChildren ? "md" : "full"}
            // size={btnChildren ? "md" : "sm"}
            size="sm"
          >
            {btnChildren}
            {logo2 ? (
              <ChevronDown width={25} />
            ) : (
              <DotsVerticalIcon
                className={
                  "transition-all " +
                  (buttonHovered
                    ? "opacity-100"
                    : "w-[20px] min-w-[20px] opacity-0")
                }
                width={20}
              />
            )}
          </Button>
        </DropdownTrigger>
        <DropdownMenu aria-label="Static Actions">
          <DropdownItem key="star" textValue="Star" onPress={handleStarToggle}>
            <div className="flex flex-row items-center justify-between gap-2">
              <Star color="white" width={16} />
              {starred ? "Remove" : "Add"} star
            </div>
          </DropdownItem>
          <DropdownItem
            key="edit"
            textValue="Rename"
            onPress={() => openModal("edit")}
          >
            <div className="flex flex-row items-center justify-between gap-2">
              <PencilRenameIcon color="white" width={16} />
              Rename
            </div>
          </DropdownItem>
          <DropdownItem
            key="delete"
            className="text-danger"
            color="danger"
            textValue="Delete"
            onMouseOut={() => setDangerStateHovered(false)}
            onMouseOver={() => setDangerStateHovered(true)}
            onPress={() => openModal("delete")}
          >
            <div className="flex flex-row items-center justify-between gap-2">
              <Trash color={dangerStateHovered ? "white" : "red"} width={16} />
              Delete
            </div>
          </DropdownItem>
        </DropdownMenu>
      </Dropdown>

      <Modal
        className="text-foreground dark"
        isOpen={isOpen}
        onOpenChange={setIsOpen}
      >
        <ModalContent>
          {modalAction === "edit" ? (
            <>
              <ModalHeader className="pb-0">Rename Conversation</ModalHeader>
              <ModalBody>
                <Input
                  label={
                    <div className="space-x-1 text-xs">
                      <span>Previous Name</span>
                      <b>{chatName}</b>
                    </div>
                  }
                  labelPlacement="outside"
                  placeholder="Enter new chat name"
                  size="lg"
                  type="text"
                  value={newName}
                  variant="faded"
                  onChange={(e: {
                    target: { value: SetStateAction<string> };
                  }) => setNewName(e.target.value)}
                  onKeyDown={(e: { key: string }) => {
                    if (e.key == "Enter") handleEdit();
                  }}
                />
              </ModalBody>
              <ModalFooter>
                <Button variant="light" onPress={() => setIsOpen(false)}>
                  Cancel
                </Button>
                <Button color="primary" onPress={handleEdit}>
                  Save
                </Button>
              </ModalFooter>
            </>
          ) : (
            <>
              <ModalHeader className="pb-0">
                Are you sure you want to delete this chat?
              </ModalHeader>
              <ModalBody className="py-0">
                <p className="text-danger">This action cannot be undone.</p>
              </ModalBody>
              <ModalFooter>
                <Button variant="light" onPress={() => setIsOpen(false)}>
                  Cancel
                </Button>
                <Button color="danger" variant="flat" onPress={handleDelete}>
                  Delete
                </Button>
              </ModalFooter>
            </>
          )}
        </ModalContent>
      </Modal>
    </>
  );
}

import Image from "next/image";
import React, {
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
} from "react";

import { Button } from "@/components";
import { ArrowRight01Icon } from "@/components/shared/icons";
import FilePreview, {
  UploadedFilePreview,
} from "@/features/chat/components/files/FilePreview";
import FileUpload from "@/features/chat/components/files/FileUpload";
import { useLoading } from "@/features/chat/hooks/useLoading";
import { useSendMessage } from "@/features/chat/hooks/useSendMessage";
import { useWorkflowSelection } from "@/features/chat/hooks/useWorkflowSelection";
import { useIntegrations } from "@/features/integrations/hooks/useIntegrations";
import {
  useComposerFiles,
  useComposerModeSelection,
  useComposerTextActions,
  useComposerUI,
  useInputText,
} from "@/stores/composerStore";
import { useWorkflowSelectionStore } from "@/stores/workflowSelectionStore";
import { FileData, SearchMode } from "@/types/shared";

import ComposerInput, { ComposerInputRef } from "./ComposerInput";
import ComposerToolbar from "./ComposerToolbar";
import SelectedToolIndicator from "./SelectedToolIndicator";
import SelectedWorkflowIndicator from "./SelectedWorkflowIndicator";

interface MainSearchbarProps {
  scrollToBottom: () => void;
  inputRef: React.RefObject<HTMLTextAreaElement | null>;
  fileUploadRef?: React.RefObject<{
    openFileUploadModal: () => void;
    handleDroppedFiles: (files: File[]) => void;
  } | null>;
  appendToInputRef?: React.RefObject<((text: string) => void) | null>;
  droppedFiles?: File[];
  onDroppedFilesProcessed?: () => void;
  hasMessages: boolean;
}

const Composer: React.FC<MainSearchbarProps> = ({
  scrollToBottom,
  inputRef,
  fileUploadRef,
  appendToInputRef,
  droppedFiles,
  onDroppedFilesProcessed,
  hasMessages,
}) => {
  const [currentHeight, setCurrentHeight] = useState<number>(24);
  const composerInputRef = useRef<ComposerInputRef>(null);
  const inputText = useInputText();
  const { setInputText, clearInputText } = useComposerTextActions();
  const {
    selectedMode,
    selectedTool,
    selectedToolCategory,
    setSelectedMode,
    setSelectedTool,
    setSelectedToolCategory,
    clearToolSelection,
  } = useComposerModeSelection();
  const {
    fileUploadModal,
    uploadedFiles,
    uploadedFileData,
    pendingDroppedFiles,
    setFileUploadModal,
    setUploadedFiles,
    setUploadedFileData,
    setPendingDroppedFiles,
    removeUploadedFile,
    clearAllFiles,
  } = useComposerFiles();
  const { isSlashCommandDropdownOpen, setIsSlashCommandDropdownOpen } =
    useComposerUI();
  const { autoSend, setAutoSend } = useWorkflowSelectionStore();

  const sendMessage = useSendMessage();
  const { isLoading, setIsLoading } = useLoading();
  const { integrations, isLoading: integrationsLoading } = useIntegrations();
  const { selectedWorkflow, clearSelectedWorkflow } = useWorkflowSelection();
  const currentMode = useMemo(
    () => Array.from(selectedMode)[0],
    [selectedMode],
  );

  // When workflow is selected, handle auto-send with a brief delay to allow UI to update
  useEffect(() => {
    if (!(selectedWorkflow && autoSend)) return;
    setAutoSend(false);
    setIsLoading(true);
    sendMessage("Run this workflow", [], null, null, selectedWorkflow);
    clearSelectedWorkflow();

    if (inputRef.current) inputRef.current.focus();

    // Scroll to show the composer instead of bottom when workflow runs
    setTimeout(() => {
      if (inputRef.current) {
        inputRef.current.scrollIntoView({
          behavior: "smooth",
          block: "center",
        });
      }
    }, 200); // Small delay to allow message to render
  }, [
    selectedWorkflow,
    autoSend,
    setAutoSend,
    sendMessage,
    setIsLoading,
    clearSelectedWorkflow,
    inputRef,
  ]);

  // Expose file upload functions to parent component via ref
  useImperativeHandle(
    fileUploadRef,
    () => ({
      openFileUploadModal: () => {
        setFileUploadModal(true);
      },
      handleDroppedFiles: (files: File[]) => {
        setPendingDroppedFiles(files);
      },
    }),
    [],
  );

  // Process dropped files when the upload modal opens
  useEffect(() => {
    if (fileUploadModal && pendingDroppedFiles.length > 0) {
      // We'll handle this in the FileUpload component
      // Just clear the pending files here after the modal is opened
      setPendingDroppedFiles([]);
      if (onDroppedFilesProcessed) {
        onDroppedFilesProcessed();
      }
    }
  }, [fileUploadModal, pendingDroppedFiles, onDroppedFilesProcessed]);

  // Process any droppedFiles passed from parent when they change
  useEffect(() => {
    if (droppedFiles && droppedFiles.length > 0) {
      setPendingDroppedFiles(droppedFiles);
      setFileUploadModal(true);
    }
  }, [droppedFiles]);

  const handleFormSubmit = (e?: React.FormEvent<HTMLFormElement>) => {
    if (e) e.preventDefault();
    // Only prevent submission if there's no text AND no files AND no selected tool AND no selected workflow
    if (
      !inputText &&
      uploadedFiles.length === 0 &&
      !selectedTool &&
      !selectedWorkflow
    ) {
      return;
    }
    setIsLoading(true);

    sendMessage(
      inputText,
      uploadedFileData,
      selectedTool,
      selectedToolCategory,
      selectedWorkflow,
    );

    clearInputText();
    clearAllFiles();
    clearToolSelection();
    clearSelectedWorkflow();

    if (inputRef) inputRef.current?.focus();
    scrollToBottom();
  };

  const handleKeyDown: React.KeyboardEventHandler<HTMLInputElement> = (
    event,
  ) => {
    if (event.key === "Enter" && !event.shiftKey && !isLoading) {
      event.preventDefault();
      handleFormSubmit();
    }
  };

  const openFileUploadModal = () => {
    setFileUploadModal(true);
  };

  const handleSelectionChange = (mode: SearchMode) => {
    if (currentMode === mode) setSelectedMode(new Set([null]));
    else setSelectedMode(new Set([mode]));
    // Clear selected tool when mode changes
    setSelectedTool(null);
    setSelectedToolCategory(null);
    // Clear selected workflow when mode changes
    clearSelectedWorkflow();
    // If the user selects upload_file mode, open the file selector immediately
    if (mode === "upload_file")
      setTimeout(() => {
        openFileUploadModal();
      }, 100);
  };

  const handleSlashCommandSelect = (toolName: string, toolCategory: string) => {
    setSelectedTool(toolName);
    setSelectedToolCategory(toolCategory);
    // Clear the current mode when a tool is selected via slash command
    setSelectedMode(new Set([null]));
    // Clear selected workflow when tool is selected
    clearSelectedWorkflow();
  };

  const handleRemoveSelectedTool = () => {
    setSelectedTool(null);
    setSelectedToolCategory(null);
  };

  const handleToggleSlashCommandDropdown = () => {
    // Focus the input first - this will naturally trigger slash command detection
    if (inputRef.current) {
      inputRef.current.focus();
    }

    composerInputRef.current?.toggleSlashCommandDropdown();
    // Update the state to reflect the current dropdown state
    setIsSlashCommandDropdownOpen(
      composerInputRef.current?.isSlashCommandDropdownOpen() || false,
    );
  };

  // Sync the state with the actual dropdown state
  useEffect(() => {
    const interval = setInterval(() => {
      const isOpen =
        composerInputRef.current?.isSlashCommandDropdownOpen() || false;
      setIsSlashCommandDropdownOpen(isOpen);
    }, 100);

    return () => clearInterval(interval);
  }, []);

  const handleFilesUploaded = (files: UploadedFilePreview[]) => {
    if (files.length === 0) {
      // If no files, just clear the uploaded files
      setUploadedFiles([]);
      setUploadedFileData([]);
      return;
    }

    // Check if these are temporary files (with loading state) or final uploaded files
    const tempFiles = files.some((file) => file.isUploading);

    if (tempFiles) {
      // These are temporary files with loading state, just set them
      setUploadedFiles(files);
      return;
    }
    // These are the final uploaded files, replace temp files with final versions
    setUploadedFiles(
      files.map((file) => {
        // Find the corresponding final file (if any)
        const finalFile = files.find((f) => f.tempId === file.id);
        // If found, return the final file, otherwise keep the previous file
        return finalFile || file;
      }),
    );

    // Now process the complete file data from the response
    const fileDataArray = files.map((file) => {
      // For files that have complete response data (not temp files):
      // Use the data from the API response, including description and message
      return {
        fileId: file.id,
        url: file.url,
        filename: file.name,
        description: file.description || `File: ${file.name}`,
        type: file.type,
        message: file.message || "File uploaded successfully",
      } as FileData;
    });

    // Store the complete file data
    setUploadedFileData(fileDataArray);
  };

  // Handle paste event for images
  const handlePaste = (e: ClipboardEvent) => {
    const items = e.clipboardData?.items;
    if (!items) return;
    for (let i = 0; i < items.length; i++) {
      if (items[i].type.indexOf("image") !== -1) {
        const file = items[i].getAsFile();
        if (file) {
          e.preventDefault();
          // Open the file upload modal with the pasted image
          setFileUploadModal(true);
          setPendingDroppedFiles([file]); // Store the pasted file
          break;
        }
      }
    }
  };

  // Add paste event listener for images
  useEffect(() => {
    document.addEventListener("paste", handlePaste);
    return () => {
      document.removeEventListener("paste", handlePaste);
    };
  }, []);

  // Function to append text to the input
  const appendToInput = (text: string) => {
    const currentText = inputText;
    const newText = currentText ? `${currentText} ${text}` : text;
    setInputText(newText);
    // Focus the input after appending
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };

  // Expose appendToInput function to parent via ref
  useImperativeHandle(appendToInputRef, () => appendToInput, [appendToInput]);

  return (
    <div className="searchbar_container relative pb-1">
      {!integrationsLoading && integrations.length > 0 && !hasMessages && (
        <Button
          className="absolute -top-4 z-[0] flex h-fit w-[92%] rounded-full bg-zinc-800/40 px-4 py-2 pb-8 text-xs text-foreground-300 hover:bg-zinc-800/70 hover:text-zinc-400 sm:w-[46%]"
          onClick={handleToggleSlashCommandDropdown}
        >
          <div className="flex w-full items-center justify-between">
            <span className="text-xs">Connect your tools to GAIA</span>
            <div className="ml-3 flex items-center gap-1">
              {integrations.slice(0, 8).map((integration) => (
                <div
                  key={integration.id}
                  className="opacity-60 transition duration-200 hover:scale-150 hover:rotate-6 hover:opacity-120"
                  title={integration.name}
                >
                  <Image
                    width={14}
                    height={14}
                    src={integration.icons[0]}
                    alt={integration.name}
                    className="h-[14px] w-[14px] object-contain"
                  />
                </div>
              ))}

              <ArrowRight01Icon width={18} height={18} className="ml-3" />
            </div>
          </div>
        </Button>
      )}
      <div className="searchbar relative z-[2] rounded-3xl bg-zinc-800 px-1 pt-1 pb-2">
        <FilePreview files={uploadedFiles} onRemove={removeUploadedFile} />
        <SelectedToolIndicator
          toolName={selectedTool}
          toolCategory={selectedToolCategory}
          onRemove={handleRemoveSelectedTool}
        />
        <SelectedWorkflowIndicator
          workflow={selectedWorkflow}
          onRemove={clearSelectedWorkflow}
        />
        <ComposerInput
          ref={composerInputRef}
          searchbarText={inputText}
          onSearchbarTextChange={setInputText}
          handleFormSubmit={handleFormSubmit}
          handleKeyDown={handleKeyDown}
          currentHeight={currentHeight}
          onHeightChange={setCurrentHeight}
          inputRef={inputRef}
          hasMessages={hasMessages}
          onSlashCommandSelect={handleSlashCommandSelect}
        />
        <ComposerToolbar
          selectedMode={selectedMode}
          openFileUploadModal={openFileUploadModal}
          handleFormSubmit={handleFormSubmit}
          searchbarText={inputText}
          handleSelectionChange={handleSelectionChange}
          selectedTool={selectedTool}
          onToggleSlashCommandDropdown={handleToggleSlashCommandDropdown}
          isSlashCommandDropdownOpen={isSlashCommandDropdownOpen}
        />
      </div>
      <FileUpload
        open={fileUploadModal}
        onOpenChange={setFileUploadModal}
        onFilesUploaded={handleFilesUploaded}
        initialFiles={pendingDroppedFiles}
        isPastedFile={pendingDroppedFiles.some((file) =>
          file.type.includes("image"),
        )}
      />
    </div>
  );
};

export default Composer;

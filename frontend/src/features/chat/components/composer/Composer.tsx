import { useParams } from "next/navigation";
import React, {
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
} from "react";

import FilePreview, {
  UploadedFilePreview,
} from "@/features/chat/components/files/FilePreview";
import FileUpload from "@/features/chat/components/files/FileUpload";
import { useLoading } from "@/features/chat/hooks/useLoading";
import { useSendMessage } from "@/features/chat/hooks/useSendMessage";
import { FileData, SearchMode } from "@/types/shared";

import ComposerInput, { ComposerInputRef } from "./ComposerInput";
import ComposerToolbar from "./ComposerToolbar";
import SelectedToolIndicator from "./SelectedToolIndicator";

interface MainSearchbarProps {
  scrollToBottom: () => void;
  inputRef: React.RefObject<HTMLTextAreaElement | null>;
  fileUploadRef?: React.MutableRefObject<{
    openFileUploadModal: () => void;
    handleDroppedFiles: (files: File[]) => void;
  } | null>;
  droppedFiles?: File[];
  onDroppedFilesProcessed?: () => void;
}

const Composer: React.FC<MainSearchbarProps> = ({
  scrollToBottom,
  inputRef,
  fileUploadRef,
  droppedFiles,
  onDroppedFilesProcessed,
}) => {
  const { id: convoIdParam } = useParams<{ id: string }>();
  const [currentHeight, setCurrentHeight] = useState<number>(24);
  const composerInputRef = useRef<ComposerInputRef>(null);
  const [searchbarText, setSearchbarText] = useState<string>("");
  const [selectedMode, setSelectedMode] = useState<Set<SearchMode>>(
    new Set([null]),
  );
  const [selectedTool, setSelectedTool] = useState<string | null>(null);
  const [selectedToolCategory, setSelectedToolCategory] = useState<
    string | null
  >(null);
  const [fileUploadModal, setFileUploadModal] = useState<boolean>(false);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFilePreview[]>([]);
  const [uploadedFileData, setUploadedFileData] = useState<FileData[]>([]);
  const [pendingDroppedFiles, setPendingDroppedFiles] = useState<File[]>([]);
  const [isSlashCommandDropdownOpen, setIsSlashCommandDropdownOpen] =
    useState(false);
  const sendMessage = useSendMessage(convoIdParam ?? null);
  const { isLoading, setIsLoading } = useLoading();
  const currentMode = useMemo(
    () => Array.from(selectedMode)[0],
    [selectedMode],
  );

  // Load saved input from localStorage on mount
  useEffect(() => {
    const savedInput = localStorage.getItem("gaia-searchbar-text");
    if (savedInput) {
      setSearchbarText(savedInput);
    }
  }, []);

  // Save input to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem("gaia-searchbar-text", searchbarText);
  }, [searchbarText]);

  // Expose functions to parent component via ref
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
    // Only prevent submission if there's no text AND no files AND no selected tool
    if (
      !searchbarText &&
      uploadedFiles.length === 0 &&
      !selectedTool
    ) {
      return;
    }
    setIsLoading(true);

    // Send the message with complete file data
    const messageText = searchbarText;

    sendMessage(
      messageText,
      currentMode,
      [], // No page fetch URLs since we removed that functionality
      uploadedFileData,
      selectedTool, // Pass the selected tool name
      selectedToolCategory, // Pass the selected tool category
    );

    // Clear uploaded files after sending
    setUploadedFiles([]);
    setUploadedFileData([]);

    // Clear selected tool after sending
    setSelectedTool(null);
    setSelectedToolCategory(null);

    // Optional: Clear the input field (can be controlled via a setting)
    const shouldClearInput =
      localStorage.getItem("gaia-clear-input-on-send") !== "false";
    if (shouldClearInput) {
      setSearchbarText("");
      localStorage.removeItem("gaia-searchbar-text"); // Clear saved text when intentionally clearing
    }

    if (inputRef) inputRef.current?.focus();
    scrollToBottom();
  };

  const handleKeyDown: React.KeyboardEventHandler<HTMLInputElement> = (
    event,
  ) => {
    if (event.key === "Enter" && event.shiftKey) {
      event.preventDefault();
      setSearchbarText((text) => `${text}\n`);
    } else if (event.key === "Enter" && !isLoading) {
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
    // If the user selects upload_file mode, open the file selector immediately
    if (mode === "upload_file") {
      setTimeout(() => {
        openFileUploadModal();
      }, 100);
    }
  };

  const handleSlashCommandSelect = (toolName: string, toolCategory: string) => {
    setSelectedTool(toolName);
    setSelectedToolCategory(toolCategory);
    // Clear the current mode when a tool is selected via slash command
    setSelectedMode(new Set([null]));
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
    setUploadedFiles((prev) => {
      // Map through the previous files
      const updatedFiles = prev.map((prevFile) => {
        // Find the corresponding final file (if any)
        const finalFile = files.find((f) => f.tempId === prevFile.id);
        // If found, return the final file, otherwise keep the previous file
        return finalFile || prevFile;
      });
      return updatedFiles;
    });

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

  const removeUploadedFile = (fileId: string) => {
    setUploadedFiles((prevFiles) =>
      prevFiles.filter((file) => file.id !== fileId),
    );
    setUploadedFileData((prevData) =>
      prevData.filter((data) => data.fileId !== fileId),
    );
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

  return (
    <>
      <div className="searchbar_container relative pb-1">
        <div className="searchbar rounded-3xl bg-zinc-800 px-1 pt-1 pb-2">
          <FilePreview files={uploadedFiles} onRemove={removeUploadedFile} />
          <SelectedToolIndicator
            toolName={selectedTool}
            toolCategory={selectedToolCategory}
            onRemove={handleRemoveSelectedTool}
          />
          <ComposerInput
            ref={composerInputRef}
            searchbarText={searchbarText}
            onSearchbarTextChange={setSearchbarText}
            handleFormSubmit={handleFormSubmit}
            handleKeyDown={handleKeyDown}
            currentHeight={currentHeight}
            onHeightChange={setCurrentHeight}
            inputRef={inputRef}
            onSlashCommandSelect={handleSlashCommandSelect}
          />
          <ComposerToolbar
            selectedMode={selectedMode}
            openFileUploadModal={openFileUploadModal}
            handleFormSubmit={handleFormSubmit}
            searchbarText={searchbarText}
            handleSelectionChange={handleSelectionChange}
            selectedTool={selectedTool}
            onToggleSlashCommandDropdown={handleToggleSlashCommandDropdown}
            isSlashCommandDropdownOpen={isSlashCommandDropdownOpen}
          />
        </div>
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
    </>
  );
};

export default Composer;

import { create } from "zustand";
import { devtools, persist } from "zustand/middleware";
import { useShallow } from "zustand/react/shallow";
import type { UploadedFilePreview } from "@/features/chat/components/files/FilePreview";
import {
  DEFAULT_DEV_COMMS_MODEL,
  DEFAULT_DEV_EXECUTOR_MODEL,
} from "@/features/chat/constants/devModels";
import { stripLocalePrefix } from "@/i18n/config";
import type {
  ReplyToMessageData,
  SelectedCalendarEventData,
  SelectedWorkflowData,
  WorkflowSelectionOptions,
} from "@/stores/composerStore.types";
import type { FileData } from "@/types/shared/fileTypes";
import type { SearchMode } from "@/types/shared/searchTypes";

interface ComposerState {
  // Text input state
  pendingPrompt: string | null;
  /**
   * Send `pendingPrompt` as the user's turn on arrival instead of dropping it
   * into the composer. Onboarding's web path uses this so the first message
   * shows up as a real user bubble with GAIA's streamed reply under it.
   */
  inputText: string;

  // Mode and tool selection
  selectedMode: Set<SearchMode>;
  selectedTool: string | null;
  selectedToolCategory: string | null;

  // File management
  uploadedFiles: UploadedFilePreview[];
  uploadedFileData: FileData[];

  // UI state
  isSlashCommandDropdownOpen: boolean;

  // Selections attached to the next message
  selectedWorkflow: SelectedWorkflowData | null;
  workflowAutoSend: boolean;
  selectedCalendarEvent: SelectedCalendarEventData | null;

  // Reply-to-message selection (never persisted: a reload must not restore a
  // reply target the user has forgotten about)
  replyToMessage: ReplyToMessageData | null;

  // DEV-ONLY model selection (chat-header selector; only used in development)
  useDefaultModels: boolean;
  commsModel: string;
  executorModel: string;
}

interface ComposerActions {
  // Text input actions
  appendToInput: (text: string) => void;
  setPendingPrompt: (prompt: string | null) => void;
  clearPendingPrompt: () => void;
  setInputText: (text: string) => void;
  appendToInputText: (text: string) => void;
  clearInputText: () => void;

  // Mode and tool actions
  setSelectedMode: (mode: Set<SearchMode>) => void;
  setSelectedTool: (tool: string | null, category?: string | null) => void;
  setSelectedToolCategory: (category: string | null) => void;
  clearToolSelection: () => void;

  // File management actions
  setUploadedFiles: (files: UploadedFilePreview[]) => void;
  addUploadedFile: (file: UploadedFilePreview) => void;
  replaceUploadedFile: (tempId: string, file: UploadedFilePreview) => void;
  removeUploadedFile: (fileId: string) => void;
  setUploadedFileData: (data: FileData[]) => void;
  addUploadedFileData: (data: FileData) => void;
  removeUploadedFileData: (fileId: string) => void;
  clearAllFiles: () => void;

  // UI actions
  setIsSlashCommandDropdownOpen: (open: boolean) => void;

  // Selection actions
  selectWorkflow: (
    workflow: SelectedWorkflowData,
    options?: WorkflowSelectionOptions,
  ) => void;
  clearSelectedWorkflow: () => void;
  selectCalendarEvent: (event: SelectedCalendarEventData) => void;
  clearSelectedCalendarEvent: () => void;

  // Reply-to-message actions
  setReplyToMessage: (message: ReplyToMessageData | null) => void;
  clearReplyToMessage: () => void;

  // DEV-ONLY model selection actions
  setUseDefaultModels: (use: boolean) => void;
  setCommsModel: (model: string) => void;
  setExecutorModel: (model: string) => void;

  // Reset actions
  resetComposer: () => void;
}

type ComposerStore = ComposerState & ComposerActions;

const initialState: ComposerState = {
  // Text input state
  pendingPrompt: null,
  inputText: "",

  // Mode and tool selection
  selectedMode: new Set([null]),
  selectedTool: null,
  selectedToolCategory: null,

  // File management
  uploadedFiles: [],
  uploadedFileData: [],

  // UI state
  isSlashCommandDropdownOpen: false,

  // Selections attached to the next message
  selectedWorkflow: null,
  workflowAutoSend: false,
  selectedCalendarEvent: null,

  // Reply-to-message selection
  replyToMessage: null,

  // DEV-ONLY model selection
  useDefaultModels: true,
  commsModel: DEFAULT_DEV_COMMS_MODEL,
  executorModel: DEFAULT_DEV_EXECUTOR_MODEL,
};

/** Bumped when the two selection stores were folded into this one. */
const COMPOSER_STORAGE_VERSION = 1;

const LEGACY_WORKFLOW_SELECTION_KEY = "workflow-selection-storage";
const LEGACY_CALENDAR_SELECTION_KEY = "calendar-event-selection-storage";

const readLegacySelectionState = (key: string): Record<string, unknown> => {
  const raw = globalThis.localStorage?.getItem(key);
  if (!raw) return {};
  const parsed: unknown = JSON.parse(raw);
  const state =
    parsed && typeof parsed === "object"
      ? (parsed as { state?: unknown }).state
      : null;
  return state && typeof state === "object"
    ? (state as Record<string, unknown>)
    : {};
};

/**
 * One-time move of the two standalone selection stores' persisted state into
 * this store. Runs after every rehydrate (a fresh install has no
 * ``composer-storage`` yet, so a version-gated ``migrate`` would never fire),
 * and is a no-op once the legacy keys are gone.
 */
const readLegacySelections = (): Partial<ComposerState> | null => {
  if (typeof globalThis.localStorage === "undefined") return null;
  const workflow = readLegacySelectionState(LEGACY_WORKFLOW_SELECTION_KEY);
  const calendar = readLegacySelectionState(LEGACY_CALENDAR_SELECTION_KEY);
  const hadLegacy =
    globalThis.localStorage.getItem(LEGACY_WORKFLOW_SELECTION_KEY) !== null ||
    globalThis.localStorage.getItem(LEGACY_CALENDAR_SELECTION_KEY) !== null;
  if (!hadLegacy) return null;
  globalThis.localStorage.removeItem(LEGACY_WORKFLOW_SELECTION_KEY);
  globalThis.localStorage.removeItem(LEGACY_CALENDAR_SELECTION_KEY);
  return {
    selectedWorkflow:
      (workflow.selectedWorkflow as SelectedWorkflowData | null) ?? null,
    workflowAutoSend: workflow.autoSend === true,
    selectedCalendarEvent:
      (calendar.selectedCalendarEvent as SelectedCalendarEventData | null) ??
      null,
  };
};

const partializeComposer = (state: ComposerStore) => ({
  inputText: state.inputText,
  pendingPrompt: state.pendingPrompt,
  useDefaultModels: state.useDefaultModels,
  commsModel: state.commsModel,
  executorModel: state.executorModel,
  // Selections persisted here to preserve the behaviour of the two
  // selection stores this slice replaced.
  selectedWorkflow: state.selectedWorkflow,
  workflowAutoSend: state.workflowAutoSend,
  selectedCalendarEvent: state.selectedCalendarEvent,
});

type PersistedComposerState = ReturnType<typeof partializeComposer>;

export const useComposerStore = create<ComposerStore>()(
  devtools(
    persist(
      (set) => ({
        ...initialState,

        // Text input actions
        appendToInput: (text) => {
          set({ pendingPrompt: text }, false, "appendToInput");
          // Navigate to chat page if not already there
          if (
            typeof window !== "undefined" &&
            stripLocalePrefix(window.location.pathname).startsWith("/c") ===
              false
          ) {
            // Use Next.js programmatic navigation
            window.location.assign("/c");
          }
        },

        setPendingPrompt: (pendingPrompt) =>
          set({ pendingPrompt }, false, "setPendingPrompt"),

        clearPendingPrompt: () => {
          set({ pendingPrompt: null }, false, "clearPendingPrompt");
        },

        setInputText: (inputText) => {
          set({ inputText }, false, "setInputText");
        },

        appendToInputText: (text) =>
          set(
            (state) => {
              const newText = state.inputText
                ? `${state.inputText} ${text}`
                : text;
              return { inputText: newText };
            },
            false,
            "appendToInputText",
          ),

        clearInputText: () => {
          set({ inputText: "" }, false, "clearInputText");
        },

        // Mode and tool actions
        setSelectedMode: (selectedMode) =>
          set({ selectedMode }, false, "setSelectedMode"),

        setSelectedTool: (selectedTool, selectedToolCategory = null) =>
          set({ selectedTool, selectedToolCategory }, false, "setSelectedTool"),

        setSelectedToolCategory: (selectedToolCategory) =>
          set({ selectedToolCategory }, false, "setSelectedToolCategory"),

        clearToolSelection: () =>
          set(
            { selectedTool: null, selectedToolCategory: null },
            false,
            "clearToolSelection",
          ),

        // File management actions
        setUploadedFiles: (uploadedFiles) =>
          set({ uploadedFiles }, false, "setUploadedFiles"),

        addUploadedFile: (file) =>
          set(
            (state) => ({ uploadedFiles: [...state.uploadedFiles, file] }),
            false,
            "addUploadedFile",
          ),

        replaceUploadedFile: (tempId, file) =>
          set(
            (state) => ({
              uploadedFiles: state.uploadedFiles.map((f) =>
                f.id === tempId ? file : f,
              ),
            }),
            false,
            "replaceUploadedFile",
          ),

        removeUploadedFile: (fileId) =>
          set(
            (state) => ({
              uploadedFiles: state.uploadedFiles.filter((f) => f.id !== fileId),
              uploadedFileData: state.uploadedFileData.filter(
                (f) => f.fileId !== fileId,
              ),
            }),
            false,
            "removeUploadedFile",
          ),

        setUploadedFileData: (uploadedFileData) =>
          set({ uploadedFileData }, false, "setUploadedFileData"),

        addUploadedFileData: (data) =>
          set(
            (state) => ({
              uploadedFileData: [...state.uploadedFileData, data],
            }),
            false,
            "addUploadedFileData",
          ),

        removeUploadedFileData: (fileId) =>
          set(
            (state) => ({
              uploadedFileData: state.uploadedFileData.filter(
                (f) => f.fileId !== fileId,
              ),
            }),
            false,
            "removeUploadedFileData",
          ),

        clearAllFiles: () =>
          set(
            {
              uploadedFiles: [],
              uploadedFileData: [],
            },
            false,
            "clearAllFiles",
          ),

        // UI actions
        setIsSlashCommandDropdownOpen: (isSlashCommandDropdownOpen) =>
          set(
            { isSlashCommandDropdownOpen },
            false,
            "setIsSlashCommandDropdownOpen",
          ),

        // Selection actions
        selectWorkflow: (selectedWorkflow, options) =>
          set(
            {
              selectedWorkflow,
              workflowAutoSend: options?.autoSend ?? false,
            },
            false,
            "selectWorkflow",
          ),

        clearSelectedWorkflow: () =>
          set(
            { selectedWorkflow: null, workflowAutoSend: false },
            false,
            "clearSelectedWorkflow",
          ),

        selectCalendarEvent: (selectedCalendarEvent) =>
          set({ selectedCalendarEvent }, false, "selectCalendarEvent"),

        clearSelectedCalendarEvent: () =>
          set(
            { selectedCalendarEvent: null },
            false,
            "clearSelectedCalendarEvent",
          ),

        // Reply-to-message actions
        setReplyToMessage: (replyToMessage) =>
          set({ replyToMessage }, false, "setReplyToMessage"),

        clearReplyToMessage: () =>
          set({ replyToMessage: null }, false, "clearReplyToMessage"),

        // DEV-ONLY model selection actions
        setUseDefaultModels: (useDefaultModels) =>
          set({ useDefaultModels }, false, "setUseDefaultModels"),
        setCommsModel: (commsModel) =>
          set({ commsModel }, false, "setCommsModel"),
        setExecutorModel: (executorModel) =>
          set({ executorModel }, false, "setExecutorModel"),

        // Reset actions
        resetComposer: () => {
          set(initialState, false, "resetComposer");
        },
      }),
      {
        name: "composer-storage",
        version: COMPOSER_STORAGE_VERSION,
        partialize: partializeComposer,
        // Older persisted shapes carry nothing that needs reshaping; without
        // a migrate, persist would drop them on a version bump.
        migrate: (persisted) => persisted as PersistedComposerState,
        // Runs inside hydration, before the store binding exists, so it must
        // not reach for `useComposerStore`; it folds the legacy keys straight
        // into the state being restored.
        merge: (persisted, current) => ({
          ...current,
          ...(persisted as Partial<ComposerStore>),
          ...(readLegacySelections() ?? {}),
        }),
      },
    ),
    { name: "composer-store" },
  ),
); // Selectors for easy access
export const usePendingPrompt = () =>
  useComposerStore((state) => state.pendingPrompt);

export const useAppendToInput = () =>
  useComposerStore((state) => state.appendToInput);

export const useInputText = () => useComposerStore((state) => state.inputText);

export const useComposerTextActions = () =>
  useComposerStore(
    useShallow((state) => ({
      setInputText: state.setInputText,
      appendToInputText: state.appendToInputText,
      clearInputText: state.clearInputText,
      clearPendingPrompt: state.clearPendingPrompt,
      setPendingPrompt: state.setPendingPrompt,
    })),
  );

export const useComposerModeSelection = () =>
  useComposerStore(
    useShallow((state) => ({
      selectedMode: state.selectedMode,
      selectedTool: state.selectedTool,
      selectedToolCategory: state.selectedToolCategory,
      setSelectedMode: state.setSelectedMode,
      setSelectedTool: state.setSelectedTool,
      setSelectedToolCategory: state.setSelectedToolCategory,
      clearToolSelection: state.clearToolSelection,
    })),
  );

export const useComposerFiles = () =>
  useComposerStore(
    useShallow((state) => ({
      uploadedFiles: state.uploadedFiles,
      uploadedFileData: state.uploadedFileData,
      setUploadedFiles: state.setUploadedFiles,
      addUploadedFile: state.addUploadedFile,
      replaceUploadedFile: state.replaceUploadedFile,
      removeUploadedFile: state.removeUploadedFile,
      setUploadedFileData: state.setUploadedFileData,
      addUploadedFileData: state.addUploadedFileData,
      removeUploadedFileData: state.removeUploadedFileData,
      clearAllFiles: state.clearAllFiles,
    })),
  );

// True while any composer file is still uploading. Send is blocked until this
// clears so a message never goes out before its attachment finishes uploading.
export const useComposerIsUploading = () =>
  useComposerStore((state) =>
    state.uploadedFiles.some((file) => file.isUploading),
  );

export const useComposerUI = () =>
  useComposerStore(
    useShallow((state) => ({
      isSlashCommandDropdownOpen: state.isSlashCommandDropdownOpen,
      setIsSlashCommandDropdownOpen: state.setIsSlashCommandDropdownOpen,
    })),
  );

export const useComposerModelSelection = () =>
  useComposerStore(
    useShallow((state) => ({
      useDefaultModels: state.useDefaultModels,
      commsModel: state.commsModel,
      executorModel: state.executorModel,
      setUseDefaultModels: state.setUseDefaultModels,
      setCommsModel: state.setCommsModel,
      setExecutorModel: state.setExecutorModel,
    })),
  );

export const useReplyToMessage = () =>
  useComposerStore(
    useShallow((state) => ({
      replyToMessage: state.replyToMessage,
      setReplyToMessage: state.setReplyToMessage,
      clearReplyToMessage: state.clearReplyToMessage,
    })),
  );

export const useSelectedWorkflow = () =>
  useComposerStore(
    useShallow((state) => ({
      selectedWorkflow: state.selectedWorkflow,
      workflowAutoSend: state.workflowAutoSend,
      selectWorkflow: state.selectWorkflow,
      clearSelectedWorkflow: state.clearSelectedWorkflow,
    })),
  );

export const useSelectedCalendarEvent = () =>
  useComposerStore(
    useShallow((state) => ({
      selectedCalendarEvent: state.selectedCalendarEvent,
      selectCalendarEvent: state.selectCalendarEvent,
      clearSelectedCalendarEvent: state.clearSelectedCalendarEvent,
    })),
  );

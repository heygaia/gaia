import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";

import { countries, Country } from "@/components/country-selector";
import { authApi } from "@/features/auth/api/authApi";

import { FIELD_NAMES, professionOptions, questions } from "../constants";
import { Message, OnboardingState } from "../types";

export const useOnboarding = () => {
  const router = useRouter();
  const [onboardingState, setOnboardingState] = useState<OnboardingState>({
    messages: [],
    currentQuestionIndex: 0,
    currentInputs: {
      text: "",
      selectedCountry: null,
      selectedProfession: null,
    },
    userResponses: {},
    isProcessing: false,
    isOnboardingComplete: false,
    hasAnsweredCurrentQuestion: false,
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const focusInput = () => {
    // Focus the input after a short delay to ensure rendering is complete
    setTimeout(() => {
      if (inputRef.current) {
        inputRef.current.focus();
      }
    }, 100);
  };

  useEffect(() => {
    scrollToBottom();

    // Focus input after each message, especially bot messages
    if (onboardingState.messages.length > 0) {
      const lastMessage =
        onboardingState.messages[onboardingState.messages.length - 1];
      if (lastMessage.type === "bot" && !onboardingState.isOnboardingComplete) {
        // Focus input after bot messages (after scroll completes)
        setTimeout(() => {
          focusInput();
        }, 300); // Wait for scroll to complete
      }
    }
  }, [onboardingState.messages, onboardingState.isOnboardingComplete]);

  const getDisplayText = useCallback(
    (fieldName: string, value: string): string => {
      switch (fieldName) {
        // case FIELD_NAMES.COUNTRY:
        //   return (
        //     countries.find((c: Country) => c.code === value)?.name || value
        //   );
        case FIELD_NAMES.PROFESSION:
          return (
            professionOptions.find((p) => p.value === value)?.label || value
          );
        default:
          return value;
      }
    },
    [],
  );

  const submitResponse = useCallback(
    (responseText: string, rawValue?: string) => {
      if (
        onboardingState.isProcessing ||
        onboardingState.currentQuestionIndex >= questions.length
      )
        return;

      const currentQuestion = questions[onboardingState.currentQuestionIndex];

      setOnboardingState((prev) => {
        const newState = { ...prev };
        newState.isProcessing = true;
        newState.hasAnsweredCurrentQuestion = true;

        const userMessage: Message = {
          id: `user-${Date.now()}`,
          type: "user",
          content: responseText,
        };
        newState.messages = [...prev.messages, userMessage];

        const newResponses = {
          ...prev.userResponses,
          [currentQuestion.fieldName]:
            rawValue !== undefined ? rawValue : responseText,
        };
        newState.userResponses = newResponses;

        newState.currentInputs = {
          text: "",
          selectedCountry: null,
          selectedProfession: null,
        };

        if (prev.currentQuestionIndex < questions.length - 1) {
          const nextQuestionIndex = prev.currentQuestionIndex + 1;

          if (prev.currentQuestionIndex === 0) {
            const greetingMessage: Message = {
              id: `greeting-${Date.now()}`,
              type: "bot",
              content: `Nice to meet you, ${newResponses.name}! 😊`,
            };
            newState.messages = [...newState.messages, greetingMessage];
          }

          const nextQuestion = questions[nextQuestionIndex];
          const botMessage: Message = {
            id: nextQuestion.id,
            type: "bot",
            content: nextQuestion.question,
          };

          newState.messages = [...newState.messages, botMessage];
          newState.currentQuestionIndex = nextQuestionIndex;
          newState.hasAnsweredCurrentQuestion = false;
        } else {
          const finalMessage: Message = {
            id: "final",
            type: "bot",
            content: `Thank you, ${newResponses.name}! I'm all set up and ready to assist you. Let's get started!`,
          };
          newState.messages = [...newState.messages, finalMessage];
          newState.isOnboardingComplete = true;
        }

        newState.isProcessing = false;
        return newState;
      });
    },
    [onboardingState.isProcessing, onboardingState.currentQuestionIndex],
  );

  const handleChipSelect = useCallback(
    (questionId: string, chipValue: string) => {
      if (
        onboardingState.isProcessing ||
        onboardingState.hasAnsweredCurrentQuestion
      )
        return;

      const currentQuestion = questions[onboardingState.currentQuestionIndex];

      // Ensure we're selecting from the current question only
      if (currentQuestion.id !== questionId) return;

      const selectedChip = currentQuestion.chipOptions?.find(
        (option) => option.value === chipValue,
      );
      if (selectedChip) {
        if (chipValue === "skip") {
          submitResponse("Skipped", "");
        } else if (chipValue === "none") {
          submitResponse("No special instructions", "");
        } else {
          submitResponse(selectedChip.label, chipValue);
        }
      }
    },
    [
      onboardingState.isProcessing,
      onboardingState.currentQuestionIndex,
      onboardingState.hasAnsweredCurrentQuestion,
      submitResponse,
    ],
  );

  const handleCountrySelect = useCallback((countryCode: string | null) => {
    // Deprecated: Country selection removed from onboarding
    console.warn("Country selection is no longer supported in onboarding");
  }, []);

  const handleProfessionSelect = useCallback(
    (professionKey: React.Key | null) => {
      if (
        onboardingState.isProcessing ||
        !professionKey ||
        typeof professionKey !== "string" ||
        !professionKey.trim()
      )
        return;

      const professionLabel = getDisplayText("profession", professionKey);
      submitResponse(professionLabel, professionKey);
    },
    [onboardingState.isProcessing, submitResponse, getDisplayText],
  );

  const handleProfessionInputChange = useCallback(
    (value: string) => {
      if (!onboardingState.isProcessing) {
        setOnboardingState((prev) => ({
          ...prev,
          currentInputs: {
            ...prev.currentInputs,
            selectedProfession: value,
          },
        }));
      }
    },
    [onboardingState.isProcessing],
  );

  const handleInputChange = useCallback(
    (value: string) => {
      if (!onboardingState.isProcessing) {
        setOnboardingState((prev) => ({
          ...prev,
          currentInputs: {
            ...prev.currentInputs,
            text: value,
          },
        }));
      }
    },
    [onboardingState.isProcessing],
  );

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();

      if (onboardingState.currentQuestionIndex >= questions.length) return;

      const currentQuestion = questions[onboardingState.currentQuestionIndex];
      const { fieldName } = currentQuestion;
      const { text } = onboardingState.currentInputs;

      // Handle different field types
      switch (fieldName) {
        // case FIELD_NAMES.COUNTRY:
        // if (selectedCountry) handleCountrySelect(selectedCountry);
        // break;

        case FIELD_NAMES.INSTRUCTIONS:
          submitResponse(text.trim() || "No specific instructions", "");
          break;

        default:
          if (text.trim()) {
            submitResponse(text.trim());
          }
          break;
      }
    },
    [
      onboardingState.currentQuestionIndex,
      onboardingState.currentInputs.text,
      submitResponse,
    ],
  );

  const handleLetsGo = async () => {
    // Prevent multiple submissions
    if (onboardingState.isProcessing) return;

    try {
      // Set loading state
      setOnboardingState((prev) => ({ ...prev, isProcessing: true }));

      // Validate required fields
      const requiredFields = [
        "name",
        // "country",
        "profession",
        "responseStyle",
      ];
      const missingFields = requiredFields.filter(
        (field) => !onboardingState.userResponses[field],
      );

      if (missingFields.length > 0) {
        toast.error(
          `Please complete all required fields: ${missingFields.join(", ")}`,
        );
        return;
      }

      // Prepare the onboarding data
      const instructions = onboardingState.userResponses.instructions?.trim();
      const onboardingData = {
        name: onboardingState.userResponses.name.trim(),
        profession: onboardingState.userResponses.profession,
        response_style: onboardingState.userResponses.responseStyle,
        instructions: instructions || null,
      };

      // Send onboarding data to backend
      const response = await authApi.completeOnboarding(onboardingData);

      if (response?.success) {
        toast.success("Welcome! Your preferences have been saved.");
        router.push("/c");
      } else {
        throw new Error("Failed to complete onboarding");
      }
    } catch (error: any) {
      console.error("Error completing onboarding:", error);

      const status = error?.response?.status;

      switch (status) {
        case 409:
          toast.error("Onboarding has already been completed.");
          router.push("/c");
          break;
        case 422:
          toast.error("Please check your input and try again.");
          break;
        default:
          toast.error("Failed to save your preferences. Please try again.");
          break;
      }
    } finally {
      // Clear loading state
      setOnboardingState((prev) => ({ ...prev, isProcessing: false }));
    }
  };

  useEffect(() => {
    const firstQuestion = questions[0];
    setOnboardingState((prev) => ({
      ...prev,
      messages: [
        {
          id: firstQuestion.id,
          type: "bot",
          content: firstQuestion.question,
        },
      ],
    }));

    // Focus input after initial message is loaded
    setTimeout(() => {
      focusInput();
    }, 500);
  }, []);

  return {
    onboardingState,
    messagesEndRef,
    inputRef,
    handleChipSelect,
    handleCountrySelect,
    handleProfessionSelect,
    handleProfessionInputChange,
    handleInputChange,
    handleSubmit,
    handleLetsGo,
  };
};

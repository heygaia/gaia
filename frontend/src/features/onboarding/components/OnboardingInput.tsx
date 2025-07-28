import { Autocomplete, AutocompleteItem } from "@heroui/autocomplete";
import { Button } from "@heroui/button";
import { Input } from "@heroui/input";
import { Kbd } from "@heroui/react";
import { useEffect, useRef } from "react";

import { SentIcon } from "@/components/shared/icons";
import { cn } from "@/lib/utils";

import { FIELD_NAMES, professionOptions, questions } from "../constants";
import { OnboardingState } from "../types";

interface OnboardingInputProps {
  onboardingState: OnboardingState;
  onSubmit: (e: React.FormEvent) => void;
  onInputChange: (value: string) => void;
  onCountrySelect: (countryCode: string | null) => void;
  onProfessionSelect: (professionKey: React.Key | null) => void;
  onProfessionInputChange: (value: string) => void;
  inputRef: React.RefObject<HTMLInputElement | null>;
}

export const OnboardingInput = ({
  onboardingState,
  onSubmit,
  onInputChange,
  onCountrySelect,
  onProfessionSelect,
  onProfessionInputChange,
  inputRef,
}: OnboardingInputProps) => {
  const countryRef = useRef<HTMLInputElement>(null);
  const professionRef = useRef<HTMLInputElement>(null);

  const currentQuestion =
    onboardingState.currentQuestionIndex < questions.length
      ? questions[onboardingState.currentQuestionIndex]
      : null;

  // Focus the appropriate input when the question changes
  useEffect(() => {
    const focusTimeout = setTimeout(() => {
      if (currentQuestion?.fieldName === FIELD_NAMES.PROFESSION) {
        // Autocomplete uses an input that we can focus
        const professionInput = document.querySelector(
          '[data-slot="autocomplete"] input',
        ) as HTMLInputElement;
        if (professionInput) professionInput.focus();
      } else if (inputRef.current)
        // Regular input
        inputRef.current.focus();
    }, 150); // Small delay to ensure the input is rendered

    return () => clearTimeout(focusTimeout);
  }, [
    currentQuestion?.fieldName,
    onboardingState.currentQuestionIndex,
    inputRef,
  ]);

  if (!currentQuestion) return null;

  const renderInput = () => {
    switch (currentQuestion.fieldName) {
      // case FIELD_NAMES.COUNTRY:
      //   return (
      //     <CountrySelector
      //       key={`country-${onboardingState.currentQuestionIndex}`}
      //       selectedKey={onboardingState.currentInputs.selectedCountry}
      //       onSelectionChange={onCountrySelect}
      //       placeholder="Search for your country..."
      //       label=""
      //     />
      //   );

      case FIELD_NAMES.PROFESSION:
        return (
          <Autocomplete
            key={`profession-${onboardingState.currentQuestionIndex}`}
            inputValue={onboardingState.currentInputs.selectedProfession || ""}
            onInputChange={onProfessionInputChange}
            onSelectionChange={onProfessionSelect}
            onKeyDown={(e) => {
              if (
                e.key === "Enter" &&
                onboardingState.currentInputs.selectedProfession?.trim()
              ) {
                e.stopPropagation();
              }
            }}
            placeholder="Type or select your profession..."
            variant="faded"
            size="lg"
            radius="full"
            allowsCustomValue
            autoFocus
            classNames={{
              base: "w-full",
            }}
          >
            {professionOptions.map((profession) => (
              <AutocompleteItem key={profession.value}>
                {profession.label}
              </AutocompleteItem>
            ))}
          </Autocomplete>
        );

      default:
        return (
          <Input
            key={`input-${onboardingState.currentQuestionIndex}`}
            ref={inputRef}
            value={onboardingState.currentInputs.text}
            radius="full"
            onChange={(e) => onInputChange(e.target.value)}
            placeholder={currentQuestion.placeholder}
            variant="faded"
            size="lg"
            autoFocus
            classNames={{ inputWrapper: "pr-1" }}
            endContent={
              <Button
                isIconOnly
                type="submit"
                disabled={
                  currentQuestion.fieldName === FIELD_NAMES.INSTRUCTIONS
                    ? onboardingState.isProcessing
                    : !onboardingState.currentInputs.text.trim() ||
                      onboardingState.isProcessing
                }
                color="primary"
                radius="full"
                aria-label="Send message"
                className={cn(onboardingState.isProcessing && "cursor-wait")}
              >
                <SentIcon color="black" />
              </Button>
            }
          />
        );
    }
  };

  return (
    <form onSubmit={onSubmit} className="mx-auto w-full max-w-2xl">
      <div className="relative">{renderInput()}</div>
      <p className="mt-2 flex items-center justify-center space-x-1 text-center text-xs text-zinc-500">
        <span>Press</span>
        <Kbd keys={"enter"} />
        <span>to continue</span>
      </p>
    </form>
  );
};

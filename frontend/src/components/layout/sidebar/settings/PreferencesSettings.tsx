"use client";

import { Select, SelectItem, SharedSelection, Textarea } from "@heroui/react";
import { Trash2 } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";

import { CountrySelector } from "@/components/country-selector";
import { CustomResponseStyleInput } from "@/components/shared/CustomResponseStyleInput";
import { LabeledField } from "@/components/shared/FormField";
import {
  MessageMultiple02Icon,
  PencilEdit01Icon,
  UserIcon,
} from "@/components/shared/icons";
import { SettingsCard } from "@/components/shared/SettingsCard";
import { SettingsCardSimple } from "@/components/shared/SettingsCardSimple";
import { SettingsOption } from "@/components/shared/SettingsOption";
import { StatusIndicator } from "@/components/shared/StatusIndicator";
import { authApi } from "@/features/auth/api/authApi";
import { useUser } from "@/features/auth/hooks/useUser";

import { ModalAction } from "./SettingsMenu";

const responseStyleOptions = [
  { value: "brief", label: "Brief - Keep responses concise and to the point" },
  { value: "detailed", label: "Detailed - Provide comprehensive explanations" },
  { value: "casual", label: "Casual - Use a friendly and informal tone" },
  {
    value: "professional",
    label: "Professional - Maintain a formal and business-like tone",
  },
  { value: "other", label: "Other - Define your own response style" },
];

const professionOptions = [
  { value: "student", label: "Student" },
  { value: "developer", label: "Software Developer" },
  { value: "designer", label: "Designer" },
  { value: "manager", label: "Manager" },
  { value: "entrepreneur", label: "Entrepreneur" },
  { value: "consultant", label: "Consultant" },
  { value: "researcher", label: "Researcher" },
  { value: "teacher", label: "Teacher" },
  { value: "writer", label: "Writer" },
  { value: "analyst", label: "Analyst" },
  { value: "engineer", label: "Engineer" },
  { value: "marketer", label: "Marketer" },
  { value: "other", label: "Other" },
];

export default function PreferencesSettings({
  setModalAction,
}: {
  setModalAction: React.Dispatch<React.SetStateAction<ModalAction | null>>;
}) {
  const user = useUser();
  const [isUpdating, setIsUpdating] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [preferences, setPreferences] = useState({
    country: user.onboarding?.preferences?.country || "",
    profession: user.onboarding?.preferences?.profession || "",
    response_style: user.onboarding?.preferences?.response_style || "",
    custom_instructions:
      user.onboarding?.preferences?.custom_instructions || null,
  });

  const updateTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const lastSavedPreferences = useRef(preferences);

  // Update preferences when user data changes
  useEffect(() => {
    const newPreferences = {
      country: user.onboarding?.preferences?.country || "",
      profession: user.onboarding?.preferences?.profession || "",
      response_style: user.onboarding?.preferences?.response_style || "",
      custom_instructions:
        user.onboarding?.preferences?.custom_instructions || null,
    };
    setPreferences(newPreferences);
    lastSavedPreferences.current = newPreferences;
  }, [user.onboarding?.preferences]);

  const updatePreferences = useCallback(
    async (updatedPreferences: typeof preferences) => {
      try {
        setIsUpdating(true);
        setHasUnsavedChanges(false);

        // Filter out empty strings and only send valid values
        const sanitizedPreferences = Object.entries(updatedPreferences).reduce(
          (acc, [key, value]) => {
            // Only include non-empty values, convert empty strings to undefined
            if (value !== "" && value !== null && value !== undefined)
              acc[key] = value;
            else if (value === null) acc[key] = null;
            // Explicitly include null values (for custom_instructions)

            return acc;
          },
          {} as Record<string, string | null>,
        );

        const response = await authApi.updatePreferences(sanitizedPreferences);

        if (response.success) {
          toast.success("Preferences saved");
          lastSavedPreferences.current = updatedPreferences;
        } else {
          // Rollback on failure
          setPreferences(lastSavedPreferences.current);
          setHasUnsavedChanges(true);
          toast.error("Failed to save preferences");
        }
      } catch (error) {
        console.error("Error updating preferences:", error);
        // Rollback on failure
        setPreferences(lastSavedPreferences.current);
        setHasUnsavedChanges(true);
        toast.error("Failed to save preferences");
      } finally {
        setIsUpdating(false);
      }
    },
    [],
  );

  // Debounced update function
  const debouncedUpdate = useCallback(
    (updatedPreferences: typeof preferences) => {
      if (updateTimeoutRef.current) {
        clearTimeout(updateTimeoutRef.current);
      }

      setHasUnsavedChanges(true);

      updateTimeoutRef.current = setTimeout(() => {
        updatePreferences(updatedPreferences);
      }, 1000); // Wait 1 second after user stops typing
    },
    [updatePreferences],
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (updateTimeoutRef.current) {
        clearTimeout(updateTimeoutRef.current);
      }
    };
  }, []);

  const handleCountryChange = (countryCode: string | null) => {
    if (countryCode) {
      // Ensure country code is uppercase
      const normalizedCode = countryCode.toUpperCase();
      const updatedPreferences = { ...preferences, country: normalizedCode };
      setPreferences(updatedPreferences);
      debouncedUpdate(updatedPreferences);
    } else {
      // Handle case when country is deselected
      const updatedPreferences = { ...preferences, country: "" };
      setPreferences(updatedPreferences);
      debouncedUpdate(updatedPreferences);
    }
  };

  const handleProfessionChange = (keys: SharedSelection) => {
    if (keys !== "all" && keys.size > 0) {
      const profession = Array.from(keys)[0] as string;
      const updatedPreferences = { ...preferences, profession };
      setPreferences(updatedPreferences);
      debouncedUpdate(updatedPreferences);
    } else {
      // Handle case when profession is deselected
      const updatedPreferences = { ...preferences, profession: "" };
      setPreferences(updatedPreferences);
      debouncedUpdate(updatedPreferences);
    }
  };

  const handleResponseStyleChange = (keys: SharedSelection) => {
    if (keys !== "all" && keys.size > 0) {
      const responseStyle = Array.from(keys)[0] as string;
      const updatedPreferences = {
        ...preferences,
        response_style: responseStyle === "other" ? "custom" : responseStyle,
      };
      setPreferences(updatedPreferences);
      debouncedUpdate(updatedPreferences);
    } else {
      // Handle case when response style is deselected
      const updatedPreferences = { ...preferences, response_style: "" };
      setPreferences(updatedPreferences);
      debouncedUpdate(updatedPreferences);
    }
  };

  const handleCustomResponseStyleChange = (customStyle: string) => {
    const updatedPreferences = {
      ...preferences,
      response_style: customStyle,
    };
    setPreferences(updatedPreferences);
    debouncedUpdate(updatedPreferences);
  };

  const handleCustomInstructionsChange = (customInstructions: string) => {
    // Convert empty strings to null for backend
    const instructions =
      customInstructions.trim() === "" ? null : customInstructions;
    const updatedPreferences = {
      ...preferences,
      custom_instructions: instructions,
    };
    setPreferences(updatedPreferences);
    debouncedUpdate(updatedPreferences);
  };

  return (
    <div className="w-full space-y-6">
      <SettingsCard
        icon={<UserIcon className="h-5 w-5 text-zinc-400" />}
        title="Personal"
      >
        <div className="space-y-3">
          <LabeledField label="Country">
            <CountrySelector
              selectedKey={preferences.country}
              onSelectionChange={handleCountryChange}
              placeholder="Select your country"
              label=""
              isDisabled={isUpdating}
              variant="flat"
              radius="md"
              classNames={{
                base: "w-full",
                popoverContent: "bg-zinc-800 border-zinc-700",
                listboxWrapper: "bg-zinc-800",
                selectorButton:
                  "bg-zinc-800/50 hover:bg-zinc-700/50 border-zinc-700 data-[hover=true]:bg-zinc-700/50 min-h-[36px]",
              }}
            />
          </LabeledField>

          <LabeledField label="Profession">
            <Select
              placeholder="Select your profession"
              selectedKeys={
                preferences.profession
                  ? new Set([preferences.profession])
                  : new Set()
              }
              onSelectionChange={handleProfessionChange}
              isDisabled={isUpdating}
              classNames={{
                trigger:
                  "bg-zinc-800/50 hover:bg-zinc-700/50 cursor-pointer min-h-[36px]",
                popoverContent: "bg-zinc-800 z-50",
                listbox: "bg-zinc-800",
                value: "text-white text-sm",
              }}
            >
              {professionOptions.map((profession) => (
                <SelectItem key={profession.value}>
                  {profession.label}
                </SelectItem>
              ))}
            </Select>
          </LabeledField>
        </div>
      </SettingsCard>

      <SettingsCard
        icon={<MessageMultiple02Icon className="h-5 w-5 text-zinc-400" />}
        title="Communication Style"
      >
        <div className="space-y-3">
          <LabeledField label="Response Style">
            <Select
              placeholder="Select response style"
              selectedKeys={
                preferences.response_style
                  ? responseStyleOptions.some(
                      (option) => option.value === preferences.response_style,
                    )
                    ? new Set([preferences.response_style])
                    : new Set(["other"])
                  : new Set()
              }
              disallowEmptySelection={false}
              onSelectionChange={handleResponseStyleChange}
              isDisabled={isUpdating}
              classNames={{
                trigger:
                  "bg-zinc-800/50 hover:bg-zinc-700/50 cursor-pointer min-h-[36px]",
                popoverContent: "bg-zinc-800 z-50",
                listbox: "bg-zinc-800",
                value: "text-white text-sm",
              }}
            >
              {responseStyleOptions.map((style) => (
                <SelectItem
                  key={style.value}
                  textValue={
                    style.value.charAt(0).toUpperCase() + style.value.slice(1)
                  }
                >
                  <div>
                    <div className="text-sm font-medium">
                      {style.value.charAt(0).toUpperCase() +
                        style.value.slice(1)}
                    </div>
                    <div className="text-xs text-zinc-500">
                      {style.label.split(" - ")[1]}
                    </div>
                  </div>
                </SelectItem>
              ))}
            </Select>
          </LabeledField>

          {preferences.response_style &&
            !responseStyleOptions.some(
              (option) => option.value === preferences.response_style,
            ) && (
              <CustomResponseStyleInput
                value={preferences.response_style}
                onChange={handleCustomResponseStyleChange}
                isDisabled={isUpdating}
              />
            )}
        </div>
      </SettingsCard>

      <SettingsCard
        icon={<PencilEdit01Icon className="h-6 w-6 text-zinc-400" />}
        title="Custom Instructions"
      >
        <div className="space-y-1">
          <Textarea
            placeholder="Add any specific instructions for how GAIA should assist you..."
            value={preferences.custom_instructions || ""}
            onChange={(e) => handleCustomInstructionsChange(e.target.value)}
            isDisabled={isUpdating}
            minRows={3}
            classNames={{
              input: "bg-zinc-800/50 text-sm",
              inputWrapper: "bg-zinc-800/50 hover:bg-zinc-700/50",
            }}
          />
          <p className="text-xs text-zinc-500">
            These instructions will be included in every conversation to
            personalize GAIA's responses.
          </p>
        </div>
      </SettingsCard>

      <SettingsCardSimple>
        <SettingsOption
          icon={<Trash2 className="h-5 w-5 text-red-500" />}
          title="Clear Chat History"
          description="Permanently delete all your conversations and chat history"
          action={
            <button
              onClick={() => setModalAction("clear_chats")}
              className="rounded-lg bg-red-500/10 px-3 py-1.5 text-xs font-medium text-red-400 transition-colors duration-200 hover:bg-red-500/20"
            >
              Clear All
            </button>
          }
        />
      </SettingsCardSimple>

      <StatusIndicator
        isUpdating={isUpdating}
        hasUnsavedChanges={hasUnsavedChanges}
      />
    </div>
  );
}

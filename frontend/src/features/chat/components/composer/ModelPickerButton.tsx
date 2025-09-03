import {
  Avatar,
  Chip,
  Select,
  SelectItem,
  SharedSelection,
} from "@heroui/react";
import { Cpu } from "lucide-react";
import React from "react";

import { useUser, useUserActions } from "@/features/auth/hooks/useUser";

import {
  useCurrentUserModel,
  useModels,
  useSelectModel,
} from "../../hooks/useModels";

const ModelPickerButton: React.FC = () => {
  const { data: models, isLoading } = useModels();
  const selectModelMutation = useSelectModel();
  const currentModel = useCurrentUserModel();
  const user = useUser();
  const { setUser } = useUserActions();

  const handleSelectionChange = (keys: SharedSelection) => {
    const selectedKey = Array.from(keys)[0];
    if (selectedKey && typeof selectedKey === "string") {
      selectModelMutation.mutate(selectedKey);
      setUser({
        ...user,
        selected_model: selectedKey,
      });
    }
  };

  const getTierDisplayName = (tier: string) => {
    return tier.charAt(0).toUpperCase() + tier.slice(1);
  };

  const getTierColor = (tier: string) => {
    switch (tier.toLowerCase()) {
      case "pro":
        return "text-amber-400";
      default:
        return "text-zinc-400";
    }
  };

  // Don't render the button if models are still loading or not available
  if (isLoading || !models || models.length === 0) {
    return null;
  }

  return (
    <Select
      placeholder="Model"
      selectedKeys={
        currentModel?.model_id ? new Set([currentModel.model_id]) : new Set()
      }
      onSelectionChange={handleSelectionChange}
      isDisabled={selectModelMutation.isPending}
      size="sm"
      radius="sm"
      variant="flat"
      aria-label="Select AI Model"
      className="w-auto max-w-[280px] min-w-[160px]"
      classNames={{
        popoverContent:
          "bg-zinc-800 border-zinc-600 min-w-[320px] max-h-[300px] overflow-auto",
        value: "text-zinc-300 text-xs font-medium",
        selectorIcon: "text-zinc-400 w-3 h-3",
      }}
      startContent={
        currentModel?.logo_url ? (
          <Avatar
            src={currentModel.logo_url}
            alt={currentModel.name}
            className="h-3 w-3 shrink-0"
            classNames={{
              img: `object-contain ${currentModel.name.toLowerCase().includes("gpt") ? "invert" : ""}`,
            }}
          />
        ) : (
          <Cpu className="h-3 w-3 shrink-0 text-zinc-400" />
        )
      }
      renderValue={(items) => {
        if (!items.length) return "Model";
        const item = items[0];
        const model = models?.find((m) => m.model_id === item.key);
        return <span className="truncate">{model?.name || "Model"}</span>;
      }}
    >
      {models
        ?.slice()
        ?.sort((a) => (currentModel?.model_id === a.model_id ? -1 : 1))
        ?.map((model) => (
          <SelectItem
            key={model.model_id}
            classNames={{
              base: "data-[hover=true]:bg-zinc-700 data-[selectable=true]:focus:bg-zinc-700 py-2 px-3 my-1 rounded-md",
              title: "text-zinc-200",
              description: "text-zinc-400 mt-1",
            }}
            startContent={
              model.logo_url ? (
                <Avatar
                  src={model.logo_url}
                  alt={model.name}
                  className="h-4 w-4 shrink-0"
                  classNames={{
                    img: `object-contain ${model.name.toLowerCase().includes("gpt") ? "invert" : ""}`,
                  }}
                />
              ) : (
                <Cpu className="h-4 w-4 shrink-0 text-zinc-400" />
              )
            }
            description={
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  {model.lowest_tier.toLowerCase() !== "free" && (
                    <span className={getTierColor(model.lowest_tier)}>
                      {getTierDisplayName(model.lowest_tier)}+ Plan
                    </span>
                  )}
                </div>
              </div>
            }
          >
            <div className="flex items-center justify-between gap-2">
              <span>{model.name}</span>
              <span className="text-xs text-zinc-500 capitalize">
                {model.model_provider}
              </span>
              {model.is_default && (
                <Chip
                  size="sm"
                  color="warning"
                  variant="flat"
                  className="text-xs"
                >
                  Default
                </Chip>
              )}
            </div>
          </SelectItem>
        )) || []}
    </Select>
  );
};

export default ModelPickerButton;

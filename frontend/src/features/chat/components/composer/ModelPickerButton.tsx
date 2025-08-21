import { Select, SelectItem, SharedSelection } from "@heroui/react";
import { Cpu } from "lucide-react";
import React from "react";

import {
  useModels,
  useSelectModel,
  useCurrentUserModel,
} from "../../hooks/useModels";
import { useUser, useUserActions } from "@/features/auth/hooks/useUser";

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

  return (
    <Select
      placeholder="Model"
      selectedKeys={
        currentModel?.model_id ? new Set([currentModel.model_id]) : new Set()
      }
      onSelectionChange={handleSelectionChange}
      isLoading={isLoading}
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
      startContent={<Cpu className="h-3 w-3 shrink-0 text-zinc-400" />}
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
            description={
              (model.supports_streaming || model.is_default) && (
                <div className="flex items-center gap-2 text-xs">
                  {model.supports_streaming && (
                    <span className="text-zinc-500">Streaming</span>
                  )}
                  {model.is_default && (
                    <span className="text-yellow-400">Default</span>
                  )}
                </div>
              )
            }
          >
            <div className="flex items-center justify-between gap-2">
              <span>{model.name}</span>
              <span className="text-xs text-zinc-500 capitalize">
                {model.provider}
              </span>
            </div>
          </SelectItem>
        )) || []}
    </Select>
  );
};

export default ModelPickerButton;

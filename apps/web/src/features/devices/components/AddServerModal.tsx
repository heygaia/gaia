"use client";

import { Button } from "@heroui/button";
import { Checkbox } from "@heroui/checkbox";
import { Input, Textarea } from "@heroui/input";
import {
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
  useDisclosure,
} from "@heroui/modal";
import { Select, SelectItem } from "@heroui/select";
import { Switch } from "@heroui/switch";
import { PlusSignIcon } from "@icons";
import type { AddOptions } from "@shared/bridge-core/config-builders";
import { useState } from "react";
import { ENTIRE_FS_PATH } from "../constants";

type ServerType = "stdio" | "url" | "filesystem";

const SERVER_TYPES: { key: ServerType; label: string; hint: string }[] = [
  {
    key: "stdio",
    label: "Command (stdio)",
    hint: "Run a local MCP server process, e.g. an npx/uvx package.",
  },
  {
    key: "url",
    label: "Local URL",
    hint: "Point at an MCP server already running on a localhost port.",
  },
  {
    key: "filesystem",
    label: "Folder access",
    hint: "Let GAIA read (and optionally write) files on this Mac.",
  },
];

const NAME_PLACEHOLDER: Record<Exclude<ServerType, "filesystem">, string> = {
  stdio: "Everything server",
  url: "Local API",
};

/** Split a textarea into trimmed, non-empty lines (env/header/path entries). */
function lines(value: string): string[] {
  return value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

interface AddServerModalProps {
  /** Sends CLI-equivalent flags to the main process; resolves true on success. */
  onAdd: (opts: AddOptions) => Promise<boolean>;
  isBusy: boolean;
}

export function AddServerModal({ onAdd, isBusy }: AddServerModalProps) {
  const { isOpen, onOpen, onOpenChange, onClose } = useDisclosure();
  const [type, setType] = useState<ServerType>("stdio");
  const [name, setName] = useState("");
  const [command, setCommand] = useState("");
  const [url, setUrl] = useState("");
  const [paths, setPaths] = useState("");
  const [pairs, setPairs] = useState("");
  const [fullFs, setFullFs] = useState(false);
  const [allowWrite, setAllowWrite] = useState(false);

  const reset = () => {
    setType("stdio");
    setName("");
    setCommand("");
    setUrl("");
    setPaths("");
    setPairs("");
    setFullFs(false);
    setAllowWrite(false);
  };

  // Folder access is a single built-in server (always "Local Files"), so it
  // needs no name; the other types key off the name the user types.
  const canSubmit =
    type === "filesystem"
      ? fullFs || lines(paths).length > 0
      : name.trim().length > 0;

  const submit = async () => {
    let opts: AddOptions;
    if (type === "stdio") {
      opts = {
        type,
        name: name.trim(),
        command: command.trim(),
        env: lines(pairs),
      };
    } else if (type === "url") {
      opts = { type, name: name.trim(), url: url.trim(), header: lines(pairs) };
    } else {
      opts = {
        type,
        path: fullFs ? [ENTIRE_FS_PATH] : lines(paths),
        write: allowWrite,
      };
    }
    if (await onAdd(opts)) {
      reset();
      onClose();
    }
  };

  const activeHint = SERVER_TYPES.find((t) => t.key === type)?.hint;

  return (
    <>
      <Button
        size="sm"
        variant="flat"
        startContent={<PlusSignIcon className="size-4" />}
        onPress={onOpen}
      >
        Add server
      </Button>
      <Modal isOpen={isOpen} onOpenChange={onOpenChange} placement="center">
        <ModalContent>
          {() => (
            <>
              <ModalHeader>Expose a server on this Mac</ModalHeader>
              <ModalBody className="gap-3">
                <Select
                  label="Type"
                  description={activeHint}
                  selectedKeys={[type]}
                  onChange={(e) => setType(e.target.value as ServerType)}
                  disallowEmptySelection
                >
                  {SERVER_TYPES.map((option) => (
                    <SelectItem key={option.key}>{option.label}</SelectItem>
                  ))}
                </Select>

                {type !== "filesystem" && (
                  <Input
                    label="Name"
                    value={name}
                    onValueChange={setName}
                    placeholder={NAME_PLACEHOLDER[type]}
                    isRequired
                  />
                )}

                {type === "stdio" && (
                  <>
                    <Input
                      label="Command"
                      value={command}
                      onValueChange={setCommand}
                      placeholder="npx -y @modelcontextprotocol/server-everything"
                    />
                    <Textarea
                      label="Environment (optional)"
                      value={pairs}
                      onValueChange={setPairs}
                      placeholder={"KEY=value\nAPI_TOKEN=..."}
                      minRows={2}
                    />
                  </>
                )}

                {type === "url" && (
                  <>
                    <Input
                      label="URL"
                      value={url}
                      onValueChange={setUrl}
                      placeholder="http://localhost:3000/mcp"
                    />
                    <Textarea
                      label="Headers (optional)"
                      value={pairs}
                      onValueChange={setPairs}
                      placeholder={"Authorization: Bearer ..."}
                      minRows={2}
                    />
                  </>
                )}

                {type === "filesystem" && (
                  <>
                    <Switch
                      size="sm"
                      isSelected={fullFs}
                      onValueChange={setFullFs}
                    >
                      Full filesystem access
                    </Switch>
                    {!fullFs && (
                      <Textarea
                        label="Folders"
                        value={paths}
                        onValueChange={setPaths}
                        placeholder={"~/Documents\n~/projects"}
                        minRows={2}
                      />
                    )}
                    <Checkbox
                      isSelected={allowWrite}
                      onValueChange={setAllowWrite}
                    >
                      Allow writes
                    </Checkbox>
                  </>
                )}
              </ModalBody>
              <ModalFooter>
                <Button variant="light" onPress={onClose}>
                  Cancel
                </Button>
                <Button
                  color="primary"
                  onPress={submit}
                  isLoading={isBusy}
                  isDisabled={!canSubmit}
                >
                  Add
                </Button>
              </ModalFooter>
            </>
          )}
        </ModalContent>
      </Modal>
    </>
  );
}

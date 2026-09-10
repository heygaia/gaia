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
import { PlusSignIcon } from "@icons";
import type { AddOptions } from "@shared/bridge-core/config-builders";
import { useState } from "react";

type ServerType = "stdio" | "url" | "filesystem";

const SERVER_TYPES: { key: ServerType; label: string }[] = [
  { key: "stdio", label: "Command (stdio)" },
  { key: "url", label: "Local URL" },
  { key: "filesystem", label: "Folder access" },
];

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
  const [allowWrite, setAllowWrite] = useState(false);

  const reset = () => {
    setType("stdio");
    setName("");
    setCommand("");
    setUrl("");
    setPaths("");
    setPairs("");
    setAllowWrite(false);
  };

  const submit = async () => {
    const opts: AddOptions = { type, name: name.trim() };
    if (type === "stdio") {
      opts.command = command.trim();
      opts.env = lines(pairs);
    } else if (type === "url") {
      opts.url = url.trim();
      opts.header = lines(pairs);
    } else {
      opts.path = lines(paths);
      opts.write = allowWrite;
    }
    if (await onAdd(opts)) {
      reset();
      onClose();
    }
  };

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
                  selectedKeys={[type]}
                  onChange={(e) => setType(e.target.value as ServerType)}
                  disallowEmptySelection
                >
                  {SERVER_TYPES.map((option) => (
                    <SelectItem key={option.key}>{option.label}</SelectItem>
                  ))}
                </Select>
                <Input
                  label="Name"
                  value={name}
                  onValueChange={setName}
                  placeholder="Everything server"
                  isRequired
                />
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
                    <Textarea
                      label="Folders"
                      value={paths}
                      onValueChange={setPaths}
                      placeholder={"~/Documents\n~/projects"}
                      minRows={2}
                    />
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
                  isDisabled={name.trim().length === 0}
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

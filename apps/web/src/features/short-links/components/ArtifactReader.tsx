"use client";

import { Spinner } from "@heroui/spinner";
import { AlertCircleIcon } from "@icons";
import { useQuery } from "@tanstack/react-query";

import RichContentRenderer from "@/features/chat/components/interface/RichContentRenderer";
import { getTodoCanvas, todoApi } from "@/features/todo/api/todoApi";

interface ArtifactReaderProps {
  todoId: string;
}

/**
 * Full-width reader for a todo's canvas — the landing surface a heygaia.link
 * short link resolves to. Renders GAIA's canvas markdown as a document.
 *
 * Auth is enforced the same way every other (main) page enforces it: the authed
 * `todoApi.getTodo` fetch 401s for a signed-out viewer, and the global response
 * interceptor opens the login modal.
 */
export default function ArtifactReader({ todoId }: ArtifactReaderProps) {
  const {
    data: todo,
    isLoading: todoLoading,
    isError: todoError,
  } = useQuery({
    queryKey: ["todo", todoId],
    queryFn: () => todoApi.getTodo(todoId),
    retry: false,
  });

  const {
    data: canvas,
    isLoading: canvasLoading,
    isError: canvasError,
  } = useQuery({
    queryKey: ["todo-canvas", todoId],
    queryFn: () => getTodoCanvas(todoId),
    retry: false,
  });

  const content = canvas?.content;

  return (
    <div className="flex h-full w-full flex-col">
      <header className="sticky top-0 z-10 shrink-0 bg-primary-bg/80 px-6 py-4 backdrop-blur-xl">
        <div className="mx-auto flex max-w-3xl items-center justify-between gap-4">
          <h1 className="min-w-0 truncate text-lg font-medium text-white">
            {todo?.title ?? "Artifact"}
          </h1>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto px-6 pb-16 pt-2">
        <div className="mx-auto max-w-3xl">
          {canvasError || todoError ? (
            <div className="flex flex-col items-center gap-2 py-24 text-center">
              <AlertCircleIcon
                width={24}
                height={24}
                className="text-red-400"
              />
              <p className="text-sm text-zinc-400">
                Couldn't load this artifact.
              </p>
            </div>
          ) : content ? (
            <RichContentRenderer content={content} className="text-base" />
          ) : canvasLoading || todoLoading ? (
            <div className="flex justify-center py-24">
              <Spinner color="default" />
            </div>
          ) : (
            <p className="py-24 text-center text-sm text-zinc-500">
              This artifact is empty.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

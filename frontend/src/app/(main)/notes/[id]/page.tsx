"use client";

import CharacterCount from "@tiptap/extension-character-count";
import Highlight from "@tiptap/extension-highlight";
import TipTapLink from "@tiptap/extension-link";
import Placeholder from "@tiptap/extension-placeholder";
import Typography from "@tiptap/extension-typography";
import Underline from "@tiptap/extension-underline";
import { EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { CircleX, TriangleAlert } from "lucide-react";
import { useParams, usePathname, useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import NotesHeader from "@/components/layout/headers/NotesHeader";
import { SaveIcon } from "@/components/shared/icons";
import { Button } from "@/components/ui/shadcn/button";
import Spinner from "@/components/ui/shadcn/spinner";
import { notesApi } from "@/features/notes/api/notesApi";
import BubbleMenuComponent from "@/features/notes/components/BubbleMenu";
import { MenuBar } from "@/features/notes/components/NotesMenuBar";
import { useHeader } from "@/hooks/layout/useHeader";
import { truncateTitle } from "@/lib/utils";

interface Note {
  id: string;
  title: string;
  content: string;
  plaintext: string;
}

export default function NotesAdd() {
  const { id } = useParams();
  const pathname = usePathname();
  const { setHeader } = useHeader();
  const router = useRouter();
  const [note, setNote] = useState<Note>({
    id: "",
    title: "",
    content: "",
    plaintext: "",
  });
  const [oldNote, setOldNote] = useState<Note>({
    id: "",
    title: "",
    content: "",
    plaintext: "",
  });
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState<boolean>(false);

  const editor = useEditor({
    extensions: [
      StarterKit,
      Highlight,
      Typography,
      Underline,
      TipTapLink.configure({
        openOnClick: true,
        autolink: true,
        linkOnPaste: true,
      }),
      CharacterCount.configure({ limit: 10_000 }),
      Placeholder.configure({
        placeholder: ({ node }) => {
          if (node.type.name === "heading") {
            return "Enter a title for your note";
          }

          return "Write something for GAIA to remember...";
        },
      }),
    ],
    content: note.content,
    onUpdate: ({ editor }) => {
      const noteContent = editor.getHTML();

      if (noteContent.length === 9500) {
        toast.custom(() => (
          <div className="flex w-full list-none flex-row items-center justify-evenly gap-3 rounded-md bg-[#ffecd8] px-4 py-2 font-medium text-nowrap text-[#dc7609]">
            <TriangleAlert
              className="min-w-[30px]"
              color="#ffecd8"
              fill="#dc7609"
              height={30}
              width={30}
            />
            <span>
              You are reaching the maximum character limit of a note. (10k
              characters)
            </span>
          </div>
        ));
      } else if (noteContent.length === 10_000) {
        toast.custom(() => (
          <div className="flex w-full list-none flex-row items-center justify-evenly gap-3 rounded-md bg-[#ffe1e1] px-4 py-2 font-medium text-nowrap text-[#e60000]">
            <CircleX
              className="min-w-[30px]"
              color="#ffe1e1"
              fill="#e60000"
              height={30}
              width={30}
            />
            <span>
              You have reached the maximum character limit of a note. (10k
              characters)
            </span>
          </div>
        ));
      }

      setNote((prev) => ({ ...prev, content: noteContent }));
    },
  });

  const unsavedChanges = useMemo(() => {
    return (
      note !== oldNote && editor?.storage?.characterCount?.characters() > 0
    );
  }, [note, oldNote, editor]);

  useEffect(() => {
    setHasUnsavedChanges(unsavedChanges);
  }, [unsavedChanges]);

  const fetchNote = useCallback(async () => {
    if (id) {
      try {
        const fetchedNote = await notesApi.fetchNoteById(id as string);

        const noteData: Note = {
          id: fetchedNote.id,
          title: fetchedNote.title || "",
          content: fetchedNote.content,
          plaintext: fetchedNote.plaintext,
        };
        setNote(noteData);
        setOldNote(noteData);
        setHasUnsavedChanges(false);
        editor?.commands.setContent(fetchedNote.content);
      } catch (error) {
        console.error("Error fetching note:", error);
      }
    }
    setIsLoading(false);
  }, [id, editor]);

  useEffect(() => {
    if (pathname === "/notes/new") {
      setIsLoading(false);
    } else {
      fetchNote();
    }
  }, [pathname, fetchNote]);

  const saveNote = async () => {
    try {
      setIsSaving(true);
      const isCreating = !id || id === "new";

      if (isCreating) {
        const response = await notesApi.createNote({
          content: note.content,
          title: note.title,
        });

        setOldNote(note);
        setHasUnsavedChanges(false);
        router.push(`/notes/${response.id}`);
      } else {
        await notesApi.updateNote(id as string, {
          content: note.content,
          title: note.title,
        });

        setOldNote(note);
        setHasUnsavedChanges(false);
      }
    } catch (error) {
      console.error("Error saving note:", error);
      toast.error("Uh oh! Something went wrong.", {
        classNames: {
          toast: "flex items-center p-3 rounded-xl gap-3 w-[350px] toast_error",
          title: " text-sm",
          description: "text-sm",
        },
        duration: 3000,
        description:
          "There was a problem with saving this Note. Please try again later.\n",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const deleteNote = useCallback(async () => {
    try {
      await notesApi.deleteNote(id as string);
      router.push("/notes");
      setHasUnsavedChanges(false);
    } catch (error) {
      console.error("Error deleting note:", error);
    }
  }, [id, router]);

  useEffect(() => {
    if (pathname.startsWith("/notes") && pathname !== "/notes") {
      setHeader(<NotesHeader onDeleteNote={deleteNote} />);
    }
  }, [deleteNote, setHeader, pathname]);

  return (
    <>
      <title id="chat_title">
        {`${truncateTitle(note.content || "New Note")} | GAIA`}
      </title>
      <div className="flex h-screen min-h-screen w-full flex-col justify-between">
        {isLoading ? (
          <div className="flex h-full items-center justify-center">
            <Spinner />
          </div>
        ) : (
          <div className="editor flex h-screen min-h-screen flex-col pt-3">
            {editor && (
              <>
                <BubbleMenuComponent editor={editor} />
                <MenuBar editor={editor} />
                <EditorContent className="min-h-screen" editor={editor} />
              </>
            )}
          </div>
        )}

        <div
          className={`fixed right-4 bottom-4 rounded-lg bg-zinc-800 p-5 shadow-lg transition-all duration-200 ${
            hasUnsavedChanges
              ? "pointer-events-auto scale-100 opacity-100"
              : "pointer-events-none scale-80 opacity-0"
          }`}
        >
          <p className="mb-2 text-lg font-medium text-white">
            You have unsaved changes!
          </p>
          <Button
            disabled={!hasUnsavedChanges || isSaving}
            className="flex gap-2 bg-[#00bbff] text-zinc-800 hover:bg-[#7bdcff]"
            onClick={saveNote}
          >
            <SaveIcon />
            {isSaving ? "Saving..." : "Save Changes"}
          </Button>
        </div>
      </div>
    </>
  );
}

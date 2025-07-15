import { Button } from "@heroui/button";
import { Textarea } from "@heroui/input";
import {
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
} from "@heroui/modal";
import { useState } from "react";
import { useEffect } from "react";
import { toast } from "sonner";

import { chatApi } from "@/features/chat/api/chatApi";
import { useConversation } from "@/features/chat/hooks/useConversation";
import { useLoading } from "@/features/chat/hooks/useLoading";
import { useLoadingText } from "@/features/chat/hooks/useLoadingText";
import { ImageData, MessageType } from "@/types/features/convoTypes";
import fetchDate from "@/utils/date/dateUtils";

interface GenerateImageProps {
  openImageDialog: boolean;
  setOpenImageDialog: (open: boolean) => void;
}

export default function GenerateImage({
  openImageDialog,
  setOpenImageDialog,
}: GenerateImageProps) {
  const { updateConvoMessages, convoMessages } = useConversation();
  const { setIsLoading } = useLoading();
  const { setLoadingText, resetLoadingText } = useLoadingText();
  const [imagePrompt, setImagePrompt] = useState("");
  const [isValid, setIsValid] = useState(true);

  useEffect(() => {
    setIsValid(imagePrompt.trim() !== "");
  }, [imagePrompt]);

  const handleInputChange = (value: string) => {
    setImagePrompt(value);
    setIsValid(value.trim() !== "");
  };

  const generateImage = async (
    prompt: string,
  ): Promise<[string, string | undefined]> => {
    try {
      const response = await chatApi.generateImage(prompt);
      return [response.url, response.improved_prompt];
    } catch (error) {
      console.error("Image generation failed:", error);
      throw new Error("Failed to generate image");
    }
  };

  const generateUniqueId = () => {
    return crypto.randomUUID();
  };

  const handleSubmit = async () => {
    if (!isValid) return;
    setIsLoading(true);
    setLoadingText("Generating Image...");

    try {
      const botMessageId = generateUniqueId();
      const userMessageId = generateUniqueId();

      const userMessage: MessageType = {
        type: "user",
        response: `Generate Image:\n${imagePrompt}`,
        date: fetchDate(),
        message_id: userMessageId,
        isConvoSystemGenerated: false,
      };

      // Create initial image_data for the loading state
      const initialImageData: ImageData = {
        url: "",
        prompt: imagePrompt,
      };

      const botLoadingMessage: MessageType = {
        type: "bot",
        response: "",
        date: fetchDate(),
        loading: true,
        image_data: initialImageData,
        message_id: botMessageId,
        isConvoSystemGenerated: false,
      };

      updateConvoMessages([...convoMessages, userMessage, botLoadingMessage]);
      setOpenImageDialog(false);

      const [imageUrl, improvedPrompt] = await generateImage(imagePrompt);

      // Create final image_data with the generated image URL
      const finalImageData: ImageData = {
        url: imageUrl,
        prompt: imagePrompt,
        improved_prompt: improvedPrompt,
      };

      const finalBotMessage: MessageType = {
        type: "bot",
        response: "Here is your generated image",
        date: fetchDate(),
        image_data: finalImageData,
        loading: false,
        message_id: botMessageId,
        isConvoSystemGenerated: false,
      };

      updateConvoMessages([...convoMessages, userMessage, finalBotMessage]);
    } catch (error) {
      toast.error("Error generating image. Please try again later.");
      console.error("Error generating image:", error);
    } finally {
      setIsLoading(false);
      resetLoadingText();
    }
  };

  return (
    <Modal
      isOpen={openImageDialog}
      onOpenChange={setOpenImageDialog}
      backdrop="opaque"
    >
      <ModalContent>
        <ModalHeader className="flex flex-col items-center">
          Generate Image
        </ModalHeader>
        <ModalBody className="flex items-center justify-center">
          <Textarea
            isRequired
            variant="faded"
            isDisabled={false}
            label="Describe the image you want to generate"
            placeholder="e.g - Futuristic city skyline"
            value={imagePrompt}
            onValueChange={handleInputChange}
          />
        </ModalBody>
        <ModalFooter className="flex w-full">
          <Button variant="flat" onPress={() => setOpenImageDialog(false)}>
            Cancel
          </Button>
          <Button color="primary" isDisabled={!isValid} onPress={handleSubmit}>
            Generate
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}

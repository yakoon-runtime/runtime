import { createContext, useContext } from "react";

type MarkdownContextType = {
  handleSubmit: (cmd: string) => void;
};

export const MarkdownContext = createContext<MarkdownContextType | undefined>(undefined);

export const useMarkdownContext = () => {
  const ctx = useContext(MarkdownContext);
  if (!ctx) throw new Error("useMarkdownContext must be used within a MarkdownContext.Provider");
  return ctx;
};

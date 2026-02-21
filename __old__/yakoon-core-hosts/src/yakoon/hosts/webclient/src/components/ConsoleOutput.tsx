import { MarkdownLine } from "./MarkdownLine";
import { useEffect, useRef } from "react";

type Props = {
  lines: string[];
};

export function ConsoleOutput({ lines }: Props) {

 const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [lines]);

  return (
    <div className="h-full p-4 bg-zinc-800 text-gray-100 font-mono space-y-2 overflow-y-auto rounded border border-zinc-700">
        {lines.map((line, i) => (
          <MarkdownLine key={i} content={line} />
        ))}
     <div ref={bottomRef} />
    </div>
  );
}
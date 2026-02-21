import { useState, useRef, useEffect } from "react";
import { InputBar } from "./components/InputBar";
import { ConsoleOutput } from "./components/ConsoleOutput";
//import { sendCommand } from "./api/yakoon-api";
import { MarkdownContext } from "./components/MarkdownContext";
import { initYakoonSocket, sendToYakoon } from "./api/yakoon-socket";


export default function App() {
  const [output, setOutput] = useState<string[]>([
    /*"> [A.M.E.E. online] SaasCommand interface ready."*/
  ]);

  const containerRef = useRef<HTMLDivElement>(null);

  const handleSubmit = (input: string) => {
    setOutput((prev) => [...prev, `> ${input}`]);
    sendToYakoon(input);
  };

  /*
  const handleSubmit = async (input: string) => {
    setOutput((prev) => [...prev, `> ${input}`]);
    const result = await sendCommand(input);
    setOutput((prev) => [...prev, result]);
  }; */

  useEffect(() => {
    // Scroll automatisch zum neuesten Output
    containerRef.current?.scrollTo(0, containerRef.current.scrollHeight);
  }, [output]);

  useEffect(() => {
    initYakoonSocket((msg: string) => {
      setOutput((prev) => [...prev, msg]);
    });
  }, []);

  return (
    <MarkdownContext.Provider value={{ handleSubmit }}>
    <div className="flex flex-col h-screen bg-zinc-900 text-gray-100">
      <header className="px-4 py-3 border-b border-zinc-700 text-lg font-semibold bg-zinc-800 shadow-sm">
        <div className="flex items-center gap-3 px-4 py-2">
          <div className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-sm shadow">
            A
          </div>
          <div>
            <h1 className="text-xl font-semibold leading-tight">A.M.E.E.</h1>
            <p className="text-sm text-gray-400">Action & Memory Execution Entity</p>
          </div>
        </div>
      </header>
      <div ref={containerRef} className="flex-1 overflow-y-auto p-4">
        <ConsoleOutput lines={output} />
      </div>
      <div className="border-t border-gray-700 p-4">
        <InputBar onSubmit={handleSubmit} />
      </div>
    </div>
    </MarkdownContext.Provider>
  );
}

import { useState } from "react";

type Props = {
  onSubmit: (input: string) => void;
  disabled?: boolean;
};

export function InputBar({ onSubmit, disabled = false }: Props) {
  const [input, setInput] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (trimmed) {
      onSubmit(trimmed);
      setInput("");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 p-2 border-zinc-700 bg-zinc-900">
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        className="flex-1 border border-zinc-700 rounded px-3 py-2 bg-zinc-800 text-gray-100 outline-none focus:ring focus:ring-blue-500"
        placeholder={disabled ? "Verbindung getrennt..." : "Befehl eingeben..."}
        disabled={disabled}
        autoFocus
      />
      <button
        type="submit"
        className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
        disabled={disabled}
      >
        OK
      </button>
    </form>
  );
}

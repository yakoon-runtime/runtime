import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Components } from "react-markdown";
import { useMarkdownContext  } from "./MarkdownContext";


type Props = {
  content: string;
};


export const consoleMarkdownTheme: Components = {
    h1: ({ children }) => (
      <h1 className="text-lg font-bold tracking-tight text-zinc-100 border-b border-zinc-700 pb-1 mb-2">
        {children}
      </h1>
    ),
    h2: ({ children }) => (
      <h2 className="text-base font-semibold text-zinc-200 mt-4 mb-1">{children}</h2>
    ),
    h3: ({ children }) => (
      <h3 className="text-sm font-semibold text-zinc-300 mt-3">{children}</h3>
    ),
    p: ({ children }) => (
      <p className="text-sm text-zinc-300 leading-snug">{children}</p>
    ),
    ul: ({ children }) => (
      <ul className="list-disc ml-5 text-sm text-zinc-300">{children}</ul>
    ),
    li: ({ children }) => (
      <li className="text-sm text-zinc-300">{children}</li>
    ),
    
    blockquote: ({ children }) => (
      <blockquote className="border-l-4 border-blue-600 pl-4 text-zinc-400 italic my-2">
        {children}
      </blockquote>
    ),
    hr: () => (
      <hr className="border-t border-zinc-700 my-3" />
    ),
    // @ts-expect-error react-markdown type for `code` is incomplete
    code: ({ inline, children }) =>
      inline ? (
        <code className="bg-zinc-700 text-yellow-300 px-1 rounded">{children}</code>
      ) : (
        <pre className="bg-zinc-800 p-2 rounded text-sm overflow-x-auto text-blue-200">
          <code>{children}</code>
        </pre>
      ),
    table: ({ children }) => (
      <table className="table-auto text-sm text-zinc-300 border-collapse">{children}</table>
    ),
    thead: ({ children }) => (
      <thead className="border-b border-zinc-700 font-semibold text-zinc-100">{children}</thead>
    ),
    td: ({ children }) => (
      <td className="px-2 py-1 border border-zinc-700">{children}</td>
    ),
    th: ({ children }) => (
      <th className="px-2 py-1 border border-zinc-700 bg-zinc-800">{children}</th>
    ),
  
    a: (props) => {
      const { handleSubmit } = useMarkdownContext(); 
      const { href, title, children } = props;

      return (
        <a
          href={href}
          title={title}
          className="text-blue-400 underline cursor-pointer"
          onClick={(e) => {
            e.preventDefault();
            if (href === "#" && title) {
              handleSubmit(title);
            } else if (href) {
              window.open(href, "_blank");
            }
          }}
        >
          {children}
        </a>
      );
    }

};


export function MarkdownLine({ content }: Props) {
  return (
    <ReactMarkdown remarkPlugins={[remarkGfm]} components={consoleMarkdownTheme}>
      {content}
    </ReactMarkdown>
  );
}

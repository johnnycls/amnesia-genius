import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export function MarkdownContent({ text }: { text: string }) {
  return <div className="prose prose-invert prose-sm max-w-none prose-p:my-2 prose-pre:my-3 prose-pre:border prose-pre:border-slate-800 prose-pre:bg-slate-950 prose-code:text-cyan-200">
    <ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown>
  </div>;
}

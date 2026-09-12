import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import Sources from "./Sources.jsx";

const components = {
  table({ children }) {
    return (
      <div className="markdown-table-wrapper">
        <table>{children}</table>
      </div>
    );
  },
};

export default function MessageBubble({ role, content, documents, isError }) {
  const isUser = role === "user";

  return (
    <div className={`message-row ${isUser ? "message-row--user" : ""}`}>
      {!isUser && <div className="message-avatar">UA</div>}

      <div className={`message-bubble ${isUser ? "message-bubble--user" : "message-bubble--assistant"} ${isError ? "message-bubble--error" : ""}`}>
        {isUser ? (
          <p>{content}</p>
        ) : (
          <div className="markdown">
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
              {content}
            </ReactMarkdown>
          </div>
        )}
        {!isUser && documents && documents.length > 0 && <Sources documents={documents} />}
      </div>
    </div>
  );
}

import { useState } from "react";

export default function Sources({ documents }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="sources">
      <button className="sources__toggle" onClick={() => setOpen((v) => !v)}>
        {open ? "Hide" : "Show"} sources ({documents.length})
      </button>

      {open && (
        <ul className="sources__list">
          {documents.map((doc, i) => {
            const metadata = doc?.metadata || {};
            const filename = metadata.filename || "Unknown document";
            const page = metadata.page_label;

            return (
              <li key={i}>
                {filename}
                {page ? ` — page ${page}` : ""}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

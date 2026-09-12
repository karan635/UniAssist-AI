export default function Sidebar({ onClear, onTalkToAdmissions }) {
  return (
    <aside className="sidebar">
      <div className="sidebar__brand">
        <span className="sidebar__mark">UA</span>
        <span className="sidebar__name">UniAssist AI</span>
      </div>

      <p className="sidebar__about">
        Ask about admissions, eligibility, fees, or placements. Answers are
        drawn from the university's official documents.
      </p>

      <button className="sidebar__action sidebar__action--primary" onClick={onTalkToAdmissions}>
        Talk to admissions
      </button>

      <button className="sidebar__action" onClick={onClear}>
        Clear conversation
      </button>
    </aside>
  );
}

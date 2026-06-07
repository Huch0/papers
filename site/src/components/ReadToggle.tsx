import { useEffect, useState } from "react";
import { getReads, isRead, setRead, setUnread } from "@/lib/reads";

// Manual mark-as-read toggle on a paper page. `mk` is the version+date marker, so the
// button reflects "unread" again after a new version / updated summary.
export default function ReadToggle({ k, mk }: { k: string; mk: string }) {
  const [r, setR] = useState(false);
  useEffect(() => { setR(isRead(getReads(), k, mk)); }, [k, mk]);
  const toggle = () => { const m = r ? setUnread(k) : setRead(k, mk); setR(isRead(m, k, mk)); };
  return (
    <button onClick={toggle}
      className="border rounded px-2 py-1 text-sm hover:border-[var(--accent)]"
      title={r ? "Mark as unread" : "Mark as read"}>
      {r ? "✓ Read — mark unread" : "Mark as read"}
    </button>
  );
}

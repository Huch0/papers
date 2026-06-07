import { useState } from "react";

export default function SortableTableIsland({
  columns, rows,
}: { columns: string[]; rows: (string | number)[][] }) {
  const [sortCol, setSortCol] = useState<number | null>(null);
  const [dir, setDir] = useState(1);

  const sorted = [...rows];
  if (sortCol !== null) {
    sorted.sort((a, b) => {
      const x = a[sortCol], y = b[sortCol];
      const nx = parseFloat(String(x).replace(/[^0-9.\-]/g, ""));
      const ny = parseFloat(String(y).replace(/[^0-9.\-]/g, ""));
      const cmp = !isNaN(nx) && !isNaN(ny) ? nx - ny : String(x).localeCompare(String(y));
      return cmp * dir;
    });
  }
  const click = (i: number) => (sortCol === i ? setDir(-dir) : (setSortCol(i), setDir(1)));

  return (
    <table className="data sortable">
      <thead>
        <tr>
          {columns.map((c, i) => (
            <th key={i} onClick={() => click(i)} style={{ cursor: "pointer", userSelect: "none" }}>
              {c}{sortCol === i ? (dir > 0 ? " ▲" : " ▼") : " ⇅"}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {sorted.map((r, ri) => (
          <tr key={ri}>{r.map((cell, ci) => <td key={ci}>{cell}</td>)}</tr>
        ))}
      </tbody>
    </table>
  );
}

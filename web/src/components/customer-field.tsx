"use client";
import { useState } from "react";
import scene from "@/data/scene.json";
// Reuses Jack's three-axis customer-field idea and his scored synthetic sales sample.
// A native range control replaces drag-only interaction so keyboard/touch both work.
export function CustomerField() {
  const [rotation, setRotation] = useState(28);
  const [selected, setSelected] = useState(0);
  const angle = (rotation * Math.PI) / 180;
  const project = (gap: number, uplift: number, tenure: number) => {
    const x = (gap / 200 - 0.45) * 260,
      z = (tenure / 24 - 0.5) * 270;
    return {
      x: 290 + x * Math.cos(angle) - z * Math.sin(angle),
      y: 220 + (x * Math.sin(angle) + z * Math.cos(angle)) * 0.4 - uplift * 13,
    };
  };
  const current = scene.rows[selected];
  return (
    <div className="field-card">
      <div className="field-top">
        <span className="eyebrow">The customer field</span>
        <span className="pill">48 sample customers</span>
      </div>
      <svg
        viewBox="0 0 580 350"
        role="img"
        aria-label="Customer field: each dot is one synthetic customer, with height showing predicted uplift. Use the customer selector below for exact scores."
      >
        {[0, 50, 100, 150, 200].map((g) => {
          const a = project(g, 0, 0),
            b = project(g, 0, 24);
          return (
            <line
              key={`g${g}`}
              x1={a.x}
              y1={a.y}
              x2={b.x}
              y2={b.y}
              stroke="#294335"
            />
          );
        })}
        {[0, 6, 12, 18, 24].map((t) => {
          const a = project(0, 0, t),
            b = project(200, 0, t);
          return (
            <line
              key={`t${t}`}
              x1={a.x}
              y1={a.y}
              x2={b.x}
              y2={b.y}
              stroke="#294335"
            />
          );
        })}
        {scene.rows.map((c, i) => {
          const p = project(c.gap, c.u, c.ten),
            floor = project(c.gap, 0, c.ten);
          return (
            <g key={c.id}>
              <line
                x1={p.x}
                y1={p.y}
                x2={floor.x}
                y2={floor.y}
                stroke={i === selected ? "#81d6a8" : "#294335"}
              />
              <circle
                cx={p.x}
                cy={p.y}
                r={i === selected ? 8 : 4}
                fill={c.u > 3 ? "#81d6a8" : "#82958a"}
                stroke={i === selected ? "#fff" : "none"}
              />
            </g>
          );
        })}
        <text x="30" y="42" fill="#b3c6b8" fontSize="12">
          ↑ More likely to return because of a message
        </text>
        <text x="350" y="326" fill="#b3c6b8" fontSize="12">
          Days since last visit →
        </text>
      </svg>
      <div className="field-controls">
        <label>
          Rotate the field
          <input
            type="range"
            min="-55"
            max="75"
            value={rotation}
            onChange={(e) => setRotation(+e.target.value)}
          />
        </label>
        <label>
          Explore a customer
          <select
            value={selected}
            onChange={(e) => setSelected(+e.target.value)}
          >
            {scene.rows.map((c, i) => (
              <option value={i} key={c.id}>
                Sample {i + 1} · {c.lab}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div className="field-insight" aria-live="polite">
        <strong>
          {current.u >= 0 ? "+" : ""}
          {current.u.toFixed(1)} points
        </strong>
        <span>
          {current.pn}% likely to visit without a message → {current.pm}% with
          one.
        </span>
      </div>
      <p className="fine">
        Real model predictions on fictional sales. This field is an
        illustration, not a live experiment. Adapted from Jack’s customer
        explorer.
      </p>
    </div>
  );
}

import React from "react";

export default function RiskGauge({ score = 0, label = "RISK INDEX" }) {
  const size = 152;
  const r = 60;
  const c = size / 2;
  const startAngle = 135;
  const angle = (Math.min(Math.max(score, 0), 100) / 100) * 270;

  const polar = (deg) => {
    const rad = (deg * Math.PI) / 180;
    return [c + r * Math.cos(rad), c + r * Math.sin(rad)];
  };

  const [sx, sy] = polar(startAngle);
  const [ex, ey] = polar(startAngle + angle);
  const [bgEx, bgEy] = polar(startAngle + 270);
  const large = angle > 180 ? 1 : 0;

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      <path
        d={`M ${sx} ${sy} A ${r} ${r} 0 1 1 ${bgEx} ${bgEy}`}
        fill="none" stroke="var(--card-3)" strokeWidth="11" strokeLinecap="round"
      />
      <path
        d={`M ${sx} ${sy} A ${r} ${r} 0 ${large} 1 ${ex} ${ey}`}
        fill="none" stroke="var(--red)" strokeWidth="11" strokeLinecap="round"
      />
      <text x={c} y={c - 3} textAnchor="middle" fontSize="27" fontWeight="600" fill="var(--text)" fontFamily="var(--font-mono)">
        {score}
      </text>
      <text x={c} y={c + 17} textAnchor="middle" fontSize="9.5" fill="var(--text-muted)" letterSpacing="0.05em">
        {label}
      </text>
    </svg>
  );
}

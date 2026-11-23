/** One drawn arrow set at the link's stroke weight, sized to the text. */
const base = {
  width: "0.8em",
  height: "0.8em",
  viewBox: "0 0 16 16",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 2.25,
  strokeLinecap: "square" as const,
  "aria-hidden": true,
  className: "inline-block shrink-0 align-[-0.05em]",
};

export const ArrowUpRight = () => (
  <svg {...base}>
    <path d="M5 11 L11 5 M6 5 H11 V10" />
  </svg>
);
export const ArrowRight = () => (
  <svg {...base}>
    <path d="M3 8 H12 M8.5 4.5 L12 8 L8.5 11.5" />
  </svg>
);
export const ArrowLeft = () => (
  <svg {...base}>
    <path d="M13 8 H4 M7.5 4.5 L4 8 L7.5 11.5" />
  </svg>
);
export const Cross = () => (
  <svg {...base}>
    <path d="M4.5 4.5 L11.5 11.5 M11.5 4.5 L4.5 11.5" />
  </svg>
);

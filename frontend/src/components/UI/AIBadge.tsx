export function AIBadge() {
  return (
    <svg
      className="ai-badge"
      viewBox="0 0 28 28"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-label="NaturalQuery AI"
    >
      <defs>
        <linearGradient id="ai-badge-grad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#06b6d4" />
          <stop offset="100%" stopColor="#6366f1" />
        </linearGradient>
      </defs>
      {/* Hexagon path (flat-top orientation) */}
      <path
        d="M14 2L25.26 8.5V21.5L14 28L2.74 21.5V8.5L14 2Z"
        fill="url(#ai-badge-grad)"
        opacity="0.15"
      />
      <path
        d="M14 2L25.26 8.5V21.5L14 28L2.74 21.5V8.5L14 2Z"
        stroke="url(#ai-badge-grad)"
        strokeWidth="1.5"
        fill="none"
      />
      {/* Spark / lightning bolt icon inside */}
      <path
        d="M15.5 8L11 15h3.5L12.5 20L18 13h-3.5L15.5 8Z"
        fill="url(#ai-badge-grad)"
      />
    </svg>
  )
}

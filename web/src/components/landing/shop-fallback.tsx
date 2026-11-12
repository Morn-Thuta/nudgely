export function ShopFallback() {
  return (
    <svg
      className="shop-fallback"
      viewBox="0 0 700 460"
      role="img"
      aria-label="Illustration of Kampung Fresh, a green-awning neighbourhood grocery shop"
    >
      <ellipse cx="350" cy="410" rx="230" ry="24" fill="#e0d6c4" />
      <path
        d="M125 158 195 118 585 138 585 390 520 420 125 395Z"
        fill="#d8c6a5"
      />
      <path d="M125 158 520 174 520 420 125 395Z" fill="#f1e3c9" />
      <path d="m125 158 70-40 390 20-65 36Z" fill="#e7d3ac" />
      <path d="m151 198 346 12 0 48-346-12Z" fill="#285b45" />
      <text
        x="324"
        y="233"
        textAnchor="middle"
        fill="#fbf3df"
        fontFamily="sans-serif"
        fontWeight="bold"
        fontSize="29"
      >
        Kampung Fresh
      </text>
      <path d="m140 255 365 12 28 43-400-16Z" fill="#285b45" />
      {[0, 1, 2, 3, 4].map((i) => (
        <path
          key={i}
          d={`m${163 + i * 73} 256 34 2 18 43-39-2Z`}
          fill="#f3e8ce"
        />
      ))}
      <path d="m150 309 103 4 0 72-103-6Z" fill="#a5c0ad" />
      <path d="m379 319 111 5 0 72-111-6Z" fill="#a5c0ad" />
      <path d="m285 314 68 4 0 87-68-5Z" fill="#285b45" />
      <path d="m295 325 48 2 0 52-48-3Z" fill="#abc4af" />
      <rect x="164" y="365" width="88" height="45" rx="4" fill="#bd9166" />
      {[0, 1, 2, 3].map((i) => (
        <circle key={i} cx={177 + i * 20} cy="365" r="12" fill="#db9457" />
      ))}
      <path d="m440 379 43 3 4 38-52-4Z" fill="#d3a56e" />
      <path
        d="M447 383v-20q15-16 29 1v20"
        fill="none"
        stroke="#926947"
        strokeWidth="4"
      />
    </svg>
  );
}

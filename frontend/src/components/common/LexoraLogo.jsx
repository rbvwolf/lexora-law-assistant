const LexoraLogo = ({ className = "h-12", light = false }) => (
  <svg viewBox="0 0 240 70" className={className} fill="none" xmlns="http://www.w3.org/2000/svg">
    <text x="0" y="50" fontFamily="Georgia, serif" fontSize="54" fill={light ? "#ffffff" : "#1a2542"} letterSpacing="-1">le</text>
    <g transform="translate(52, 10)">
      <line x1="38" y1="0" x2="2" y2="46" stroke="#c4a77d" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="4" y1="2" x2="36" y2="44" stroke={light ? "#ffffff" : "#1a2542"} strokeWidth="8" strokeLinecap="round" />
      <g transform="translate(10, 26)"><path d="M-6 8 Q0 12 6 8 L0 14 Z" fill="#c4a77d" /><line x1="-6" y1="8" x2="0" y2="0" stroke="#c4a77d" strokeWidth="1" /><line x1="6" y1="8" x2="0" y2="0" stroke="#c4a77d" strokeWidth="1" /><circle cx="0" cy="0" r="1.5" fill="#c4a77d" /></g>
      <g transform="translate(30, 26)"><path d="M-6 8 Q0 12 6 8 L0 14 Z" fill="#c4a77d" /><line x1="-6" y1="8" x2="0" y2="0" stroke="#c4a77d" strokeWidth="1" /><line x1="6" y1="8" x2="0" y2="0" stroke="#c4a77d" strokeWidth="1" /><circle cx="0" cy="0" r="1.5" fill="#c4a77d" /></g>
    </g>
    <text x="96" y="50" fontFamily="Georgia, serif" fontSize="54" fill={light ? "#ffffff" : "#1a2542"} letterSpacing="-1">ora</text>
  </svg>
);

export default LexoraLogo;

/**
 * Renders backend answer text with **bold** spans. No HTML is ever interpreted: the text is split
 * into strings and React escapes each one.
 */
const RichText = ({ text, className = '' }) => {
  const parts = String(text ?? '').split(/(\*\*[^*\n]+\*\*)/g);
  return (
    <p className={`whitespace-pre-wrap break-words ${className}`}>
      {parts.map((part, index) =>
        part.startsWith('**') && part.endsWith('**') && part.length > 4
          ? <strong key={index} className="font-bold text-navy">{part.slice(2, -2)}</strong>
          : part
      )}
    </p>
  );
};

export default RichText;

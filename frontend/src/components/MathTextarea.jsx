import { useState, useEffect } from "react";
import { MathJax } from "better-react-mathjax";

export default function MathTextarea({
  value,
  onChange,
  placeholder,
  textareaRef,
  previewRef,
}) {
  const [input, setInput] = useState(value || "");

  useEffect(() => {
    setInput(value || "");
  }, [value]);

  const handleChange = (e) => {
    const newVal = e.target.value;
    setInput(newVal);
    onChange && onChange(e);
  };

  return (
    <div className="w-full space-y-3">
      <textarea
        ref={textareaRef}
        value={input}
        onChange={handleChange}
        placeholder={placeholder}
        spellCheck={false}
        className="w-full border border-gray-300 rounded p-4 text-lg font-mono focus:outline-blue-400 min-h-[120px]"
        style={{ whiteSpace: "pre-wrap" }}
      />

      <div
        ref={previewRef}
        className="bg-gray-50 p-4 border rounded text-xl text-gray-800 min-h-[80px]"
      >
        <MathJax dynamic inline={false}>
          {"$$" + input + "$$"}
        </MathJax>
      </div>
    </div>
  );
}

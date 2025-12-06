import { useEffect, useRef, useState } from "react";
import { MathJax } from "better-react-mathjax";

const MATH_COMMANDS = [
  // Basic formatting
  {
    label: "^",
    insert: "^{}",
    cursorOffset: -1,
    title: "Superscript",
    preview: "x^2",
  },
  {
    label: "_",
    insert: "_{}",
    cursorOffset: -1,
    title: "Subscript",
    preview: "x_1",
  },
  {
    label: "\\frac",
    insert: "\\frac{}{}",
    cursorOffset: -5,
    title: "Fraction",
    preview: "\\frac{a}{b}",
  },

  // Greek letters
  { label: "\\alpha", insert: "\\alpha", title: "Alpha" },
  { label: "\\beta", insert: "\\beta", title: "Beta" },
  { label: "\\theta", insert: "\\theta", title: "Theta" },
  { label: "\\pi", insert: "\\pi", title: "Pi" },

  // Operators & Symbols
  { label: "+", insert: "+", title: "Plus" },
  { label: "-", insert: "-", title: "Minus" },
  { label: "\\cdot", insert: "\\cdot", title: "Dot Product" },
  { label: "\\div", insert: "\\div", title: "Division" },
  { label: "\\times", insert: "\\times", title: "Multiplication" },
  { label: "=", insert: "=", title: "Equals" },

  // Functions
  { label: "\\sin", insert: "\\sin", title: "Sine" },
  { label: "\\cos", insert: "\\cos", title: "Cosine" },
  { label: "\\tan", insert: "\\tan", title: "Tangent" },
  { label: "\\log", insert: "\\log", title: "Log" },
  { label: "\\ln", insert: "\\ln", title: "Natural Log" },
  {
    label: "\\sqrt{}",
    insert: "\\sqrt{}",
    cursorOffset: -1,
    title: "Square Root",
  },

  // Calculus
  { label: "\\int", insert: "\\int", title: "Integral" },
  { label: "\\sum", insert: "\\sum", title: "Summation" },
  { label: "\\lim", insert: "\\lim", title: "Limit" },
  { label: "\\nabla", insert: "\\nabla", title: "Nabla" },
  { label: "\\frac{d}{dx}", insert: "\\frac{d}{dx}", title: "Derivative" },

  // Set theory
  { label: "\\in", insert: "\\in", title: "Element of" },
  { label: "\\subset", insert: "\\subset", title: "Subset" },
  { label: "\\cup", insert: "\\cup", title: "Union" },
  { label: "\\cap", insert: "\\cap", title: "Intersection" },
  { label: "\\forall", insert: "\\forall", title: "For all" },
  { label: "\\exists", insert: "\\exists", title: "Exists" },

  // Misc
  {
    label: "\\overline{}",
    insert: "\\overline{}",
    cursorOffset: -1,
    title: "Overline",
  },
];

export default function MathInputToolbar({ targetRef }) {
  const toolbarRef = useRef();
  const [position, setPosition] = useState({ top: 0, left: 0 });

  const insertAtCursor = (insert, cursorOffset = 0) => {
    const textarea = targetRef?.current;
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const before = textarea.value.substring(0, start);
    const after = textarea.value.substring(end);

    textarea.value = before + insert + after;
    textarea.focus();

    const newPos = start + insert.length + cursorOffset;
    textarea.selectionStart = textarea.selectionEnd = newPos;
    textarea.dispatchEvent(new Event("input", { bubbles: true }));
  };

  useEffect(() => {
    const reposition = () => {
      const el = targetRef?.current;
      if (!el) return;
      const rect = el.getBoundingClientRect();
      setPosition({
        top: rect.bottom + window.scrollY + 8, // 8px below preview
        left: rect.left + window.scrollX,
      });
    };

    reposition();
    window.addEventListener("resize", reposition);
    window.addEventListener("scroll", reposition);

    return () => {
      window.removeEventListener("resize", reposition);
      window.removeEventListener("scroll", reposition);
    };
  }, [targetRef]);

  return (
    <div
      ref={toolbarRef}
      className="fixed z-50 bg-white border rounded-lg shadow-lg p-2 flex flex-wrap gap-2 w-fit max-w-[600px]"
      style={{ top: position.top, left: position.left }}
    >
      {MATH_COMMANDS.map((cmd, idx) => (
        <button
          key={idx}
          title={cmd.title}
          className="px-2 py-1 border rounded hover:bg-gray-100 text-sm"
          onClick={() => insertAtCursor(cmd.insert, cmd.cursorOffset || 0)}
        >
          <MathJax inline>{`\\(${cmd.preview || cmd.label}\\)`}</MathJax>
        </button>
      ))}
    </div>
  );
}

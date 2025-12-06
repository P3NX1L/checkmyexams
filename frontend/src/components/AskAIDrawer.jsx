// src/components/AskAIDrawer.jsx

import { useEffect, useRef, useState } from "react";
import axios from "axios";
import { MathJax } from "better-react-mathjax";

export default function AskAIDrawer({ isOpen, onClose, questionData }) {
  const drawerRef = useRef();
  const [userQuery, setUserQuery] = useState("");
  const [aiResponse, setAIResponse] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const handleOutsideClick = (e) => {
      if (drawerRef.current && !drawerRef.current.contains(e.target)) {
        onClose();
      }
    };
    if (isOpen) {
      document.addEventListener("mousedown", handleOutsideClick);
    }
    return () => {
      document.removeEventListener("mousedown", handleOutsideClick);
    };
  }, [isOpen, onClose]);

  useEffect(() => {
    if (!isOpen) {
      setUserQuery("");
      setAIResponse("");
    }
  }, [isOpen]);

  const handleSubmit = async () => {
    if (!userQuery.trim()) return;

    const payload = {
      question_latex: questionData.question_latex,
      correct_answer_latex: questionData.correct_answer_latex,
      explanation_latex: questionData.explanation_latex,
      marks: questionData.marks,
      topic: questionData.topic,
      student_answer: questionData.student_answer || "",
      comment: questionData.comment || "",
      user_message: userQuery,
      session_id: "default",
    };

    try {
      setLoading(true);
      setAIResponse("Thinking...");

      const res = await axios.post("http://localhost:8003/chat", payload);
      setAIResponse(res.data?.response || "No response from AI.");
    } catch (err) {
      setAIResponse("❌ Error fetching AI response.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className='fixed inset-0 bg-black bg-opacity-30 z-50 flex justify-end'>
      <div
        ref={drawerRef}
        className='bg-white w-full max-w-md h-full p-6 shadow-xl overflow-y-auto'
      >
        <div className='flex justify-between items-center mb-4'>
          <h2 className='text-lg font-semibold'>Ask AI</h2>
          <button
            className='text-gray-500 hover:text-gray-800'
            onClick={onClose}
          >
            ✕
          </button>
        </div>

        <div className='text-gray-800 font-medium mb-2'>Question:</div>
        <div className='bg-gray-100 p-3 rounded text-sm mb-4 whitespace-pre-wrap'>
          <MathJax>{questionData.question_latex}</MathJax>
        </div>

        <div className='mb-4'>
          <div className='text-gray-600 text-sm mb-2'>Quick Questions:</div>
          <div className='flex flex-wrap gap-2'>
            {[
              "Can you explain this question?",
              "Why is my answer wrong?",
              "Can you give me a hint?",
              "What is the correct approach?",
              "Explain the concept involved",
            ].map((msg) => (
              <button
                key={msg}
                className='bg-gray-200 hover:bg-gray-300 text-gray-800 text-xs px-3 py-1 rounded-full transition'
                onClick={() => setUserQuery(msg)}
              >
                {msg}
              </button>
            ))}
          </div>
        </div>

        <textarea
          placeholder='Type your question for AI...'
          className='w-full border border-gray-300 rounded-lg p-3 text-sm h-24 mb-4'
          value={userQuery}
          onChange={(e) => setUserQuery(e.target.value)}
        />

        <button
          className='bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700'
          onClick={handleSubmit}
          disabled={loading}
        >
          {loading ? "Asking..." : "Ask AI"}
        </button>

        {aiResponse && (
          <div className='mt-6 border-t pt-4'>
            <div className='text-gray-800 font-semibold mb-2'>
              AI's Response:
            </div>
            <div className='bg-gray-50 p-3 rounded text-sm whitespace-pre-wrap'>
              <MathJax>{aiResponse}</MathJax>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

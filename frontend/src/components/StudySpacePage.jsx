import { useParams, useNavigate } from "react-router-dom";
import { useState } from "react";
import QuestionForm from "./QuestionForm";

export default function StudySpacePage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [showQuestionForm, setShowQuestionForm] = useState(false);

  return (
    <div className='flex h-[calc(100vh-64px)]'>
      {/* Sidebar */}
      <div className='w-56 bg-gray-100 border-r p-4'>
        <button
          className='w-full bg-indigo-600 text-white py-2 rounded mb-2'
          onClick={() => setShowQuestionForm(true)}
        >
          Generate Questions
        </button>

        <button
          className='mb-4 text-lg font-semibold text-blue-700 flex items-center gap-2'
          onClick={() => navigate("/dashboard/files")}
        >
          <span>📁</span> Files
        </button>

        <button
          className='mb-4 text-lg font-semibold text-blue-700 flex items-center gap-2'
          onClick={() => navigate("/dashboard/analytics")}
        >
          📊 Analytics
        </button>

        <button
          className='w-full bg-gray-300 text-gray-800 py-2 rounded'
          onClick={() => navigate("/dashboard")}
        >
          ← Back to Study Spaces
        </button>
      </div>

      {/* Main Content */}
      <div className='flex-1 p-8'>
        {showQuestionForm ? (
          <QuestionForm studySpaceId={id} />
        ) : (
          <div className='text-gray-500 text-lg'>
            Welcome to your study space!
          </div>
        )}
      </div>
    </div>
  );
}

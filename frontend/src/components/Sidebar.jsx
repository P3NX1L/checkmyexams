// Sidebar.jsx
import { useNavigate } from "react-router-dom";

export default function Sidebar() {
  const navigate = useNavigate();
  return (
    <div className='flex flex-col w-64 bg-white border-r min-h-screen py-8 px-4'>
      <button
        className='mb-4 text-lg font-semibold text-blue-700 flex items-center gap-2'
        onClick={() => navigate("/create-questions")}
      >
        <span>📝</span> Create Questions
      </button>
      <button
        className='mb-4 text-lg font-semibold text-blue-700 flex items-center gap-2'
        onClick={() => navigate("files")}
      >
        <span>📁</span> Files
      </button>
      <button
        className='mt-auto text-lg font-semibold text-gray-600 flex items-center gap-2'
        onClick={() => navigate("/study-spaces")}
      >
        <span>⬅️</span> Back to Study Spaces
      </button>
    </div>
  );
}

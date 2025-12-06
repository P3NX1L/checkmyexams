import { useNavigate } from "react-router-dom";

export default function LandingPage() {
  const navigate = useNavigate();
  return (
    <div className='min-h-screen w-screen flex items-center justify-center bg-gradient-to-br from-blue-100 to-indigo-200'>
      <div className='bg-white p-10 rounded-xl shadow-lg w-full max-w-xl text-center flex flex-col items-center'>
        <h1 className='text-5xl font-extrabold text-indigo-700 mb-4'>
          CheckMyExams
        </h1>
        <p className='text-lg text-gray-600 mb-8'>
          Practice, evaluate, and master your exams with AI-powered question
          generation and instant feedback.
        </p>
        <button
          onClick={() => navigate("/auth")}
          className='bg-indigo-600 text-white px-8 py-3 rounded-lg font-semibold text-lg hover:bg-indigo-700 transition shadow'
        >
          Login / Sign Up
        </button>
      </div>
    </div>
  );
}

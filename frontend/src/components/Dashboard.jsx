import { useEffect, useState } from "react";
import { supabase } from "../supabaseClient";
import StudySpaces from "./StudySpaces";
import { useNavigate, Routes, Route } from "react-router-dom";
import StudySpacePage from "./StudySpacePage";
import Files from "../pages/Files";
import FileDetails from "../pages/FileDetails";
import Analytics from "../pages/Analytics";

export default function Dashboard() {
  const [user, setUser] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    supabase.auth.getUser().then(({ data }) => {
      if (!data.user) navigate("/auth");
      else {
        setUser(data.user);
        localStorage.setItem("user_id", data.user.id); // ✅ Fix
      }
    });
  }, []);

  if (!user) return <div className='p-8 text-center'>Loading...</div>;

  return (
    <div className='h-screen w-screen bg-gray-50 flex flex-col'>
      <header className='w-full bg-white shadow p-4 flex justify-between items-center'>
        <div className='text-3xl font-bold text-indigo-700'>Dashboard</div>
        <button
          className='text-sm text-gray-600 hover:text-red-600'
          onClick={async () => {
            await supabase.auth.signOut();
            navigate("/");
          }}
        >
          Logout
        </button>
      </header>
      <div className='flex flex-1 min-h-0'>
        <main className='flex-1 w-full'>
          <Routes>
            <Route
              path='/'
              element={<StudySpaces user={user} />}
            />
            <Route
              path='studyspace/:id'
              element={<StudySpacePage user={user} />}
            />
            <Route
              path='files'
              element={<Files />}
            />
            <Route
              path='files/:paperId'
              element={<FileDetails />}
            />
            <Route
              path='analytics'
              element={<Analytics />}
            />
          </Routes>
        </main>
      </div>
    </div>
  );
}

import React, { useState, useEffect } from "react";
import { supabase } from "../supabaseClient";
import { useNavigate } from "react-router-dom";

const StudySpaces = ({ user }) => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [studySpaces, setStudySpaces] = useState([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    if (user) {
      supabase
        .from("study_spaces")
        .select("*")
        .eq("user_id", user.id)
        .then(({ data }) => setStudySpaces(data || []));
    }
  }, [user]);

  const handleCreate = async () => {
    if (name.trim()) {
      const { data, error } = await supabase
        .from("study_spaces")
        .insert([{ name, description, user_id: user.id }])
        .select();
      if (!error && data) setStudySpaces([...studySpaces, ...data]);
      setIsModalOpen(false);
      setName("");
      setDescription("");
    }
  };

  return (
    <div className='flex h-[calc(100vh-64px)]'>
      <div
        className={`bg-gray-100 border-r transition-all duration-300 ease-in-out ${
          isSidebarOpen ? "w-64" : "w-16"
        }`}
      >
        <div className='flex items-center justify-between p-4 border-b'>
          {isSidebarOpen && (
            <h2 className='text-lg font-semibold'>Study Spaces</h2>
          )}
          <div className='flex gap-2 items-center'>
            <button
              onClick={() => setIsModalOpen(true)}
              className='text-lg bg-blue-500 text-white rounded-full w-7 h-7 flex items-center justify-center hover:bg-blue-600'
            >
              +
            </button>
            <button
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className='ml-2 text-gray-600 hover:text-black'
            >
              {isSidebarOpen ? "←" : "→"}
            </button>
          </div>
        </div>

        <div className='p-4'>
          {studySpaces.length === 0 ? (
            <div className='text-center text-sm text-gray-500'>
              <div className='mb-1'>No study spaces yet</div>
              {isSidebarOpen && <div>Create one to get started!</div>}
            </div>
          ) : (
            studySpaces.map((space) => (
              <div
                key={space.id}
                className='p-2 border rounded mb-2 text-sm bg-white cursor-pointer hover:bg-blue-50'
                onClick={() => {
                  localStorage.setItem("study_space_id", space.id); // ✅ Fix
                  navigate(`/dashboard/studyspace/${space.id}`);
                }}
              >
                <strong>{space.name}</strong>
                <div className='text-gray-500'>{space.description}</div>
              </div>
            ))
          )}
        </div>
      </div>

      <div className='flex-1 flex items-center justify-center text-gray-500 text-lg'>
        Select a study space to get started
      </div>

      {isModalOpen && (
        <div className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50'>
          <div className='bg-white p-6 rounded-lg w-[90%] max-w-md'>
            <h2 className='text-xl font-semibold mb-2'>
              Create New Study Space
            </h2>
            <p className='text-sm text-gray-500 mb-4'>
              Create a new study space for organizing your learning materials.
            </p>
            <div className='mb-4'>
              <label className='text-sm font-medium'>Name</label>
              <input
                type='text'
                className='w-full border rounded px-3 py-2 mt-1'
                placeholder='e.g., SAT Math, AP Biology'
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>
            <div className='mb-4'>
              <label className='text-sm font-medium'>
                Description (Optional)
              </label>
              <textarea
                className='w-full border rounded px-3 py-2 mt-1'
                placeholder='Brief description of what you are studying for...'
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>
            <div className='flex justify-end gap-3'>
              <button
                onClick={() => setIsModalOpen(false)}
                className='px-4 py-2 rounded bg-gray-200 hover:bg-gray-300 text-sm'
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                className='px-4 py-2 rounded bg-blue-600 hover:bg-blue-700 text-white text-sm'
              >
                Create Study Space
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StudySpaces;

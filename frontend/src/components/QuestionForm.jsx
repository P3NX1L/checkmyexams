import { useEffect, useState, useRef } from "react";
import { supabase } from "../supabaseClient";
import axios from "axios";
import { MathJax } from "better-react-mathjax";
import MathInputToolbar from "./MathInputToolbar";
import MathTextarea from "./MathTextarea";
import AskAIDrawer from "./AskAIDrawer"; // NEW — add this to the top imports

// Toast Component
function Toast({ message, onClose }) {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose();
    }, 3000);
    return () => clearTimeout(timer);
  }, [onClose]);

  return (
    <div className='fixed bottom-4 right-4 bg-black text-white px-4 py-2 rounded shadow-lg z-50'>
      {message}
    </div>
  );
}

export default function QuestionForm({ studySpaceId }) {
  const [showToolbar, setShowToolbar] = useState(false);
  const answerRef = useRef(null);
  const [input, setInput] = useState("");
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [feedback, setFeedback] = useState({});
  const [loading, setLoading] = useState(false);
  const [type, setType] = useState("");
  const [difficulty, setDifficulty] = useState("");
  const [current, setCurrent] = useState(0);
  const [showPreview, setShowPreview] = useState(false);
  const [paperJSON, setPaperJSON] = useState(null);
  const [showResourceMenu, setShowResourceMenu] = useState(false);
  const [numQuestions, setNumQuestions] = useState(5);
  const [file, setFile] = useState(null);
  const [showAskAIDrawer, setShowAskAIDrawer] = useState(false);
  const [askAIResponse, setAskAIResponse] = useState("");
  const [rechecking, setRechecking] = useState(false);
  const [toast, setToast] = useState(null);

  const fileInputRef = useRef();

  const handleFileUpload = () => {
    fileInputRef.current.click();
    setShowResourceMenu(false);
  };

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleGenerate = async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append("student_input", input);
    formData.append("num_questions", numQuestions);
    formData.append("type", type);
    formData.append("difficulty", JSON.stringify([difficulty || "Medium"]));
    if (file) formData.append("file", file);

    try {
      setLoading(true);
      const response = await axios.post(
        "http://localhost:8000/generate-questions/",
        formData
      );
      setQuestions(response.data);
      setAnswers({});
      setFeedback({});
      setCurrent(0);
    } catch (err) {
      alert("Error generating questions");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerChange = (idx, value) => {
    setAnswers((prev) => ({ ...prev, [idx]: value }));
  };

  const handleCheckAnswer = async (idx, q) => {
    try {
      const response = await axios.post("http://localhost:8001/check-answer", {
        question_latex: q.question_latex,
        correct_answer_latex: q.correct_answer_latex,
        explanation_latex: q.explanation_latex,
        marks: q.marks,
        topic: q.topic,
        student_answer: (answers[idx] || "").trim(),
      });
      setFeedback((prev) => ({ ...prev, [idx]: response.data }));
    } catch (err) {
      alert("Error checking answer");
      console.error(err);
    }
  };

  const handleAskAI = async () => {
    try {
      const response = await axios.post("http://localhost:9002/ask-ai", {
        question: questions[current].question_latex,
        user_answer: answers[current] || "",
      });
      setAskAIResponse(response.data?.answer || "No answer from AI.");
      setShowAskAIDrawer(true);
    } catch (error) {
      console.error("Error calling Ask AI:", error);
      setAskAIResponse("Something went wrong while asking AI.");
      setShowAskAIDrawer(true);
    }
  };

  const handleCompletePractice = async () => {
    try {
      const {
        data: { user },
      } = await supabase.auth.getUser();
      const user_id = user?.id || null;
      const title = `Practice Paper - ${new Date().toLocaleString()}`;
      const total_score = Object.values(feedback).reduce(
        (sum, f) => sum + (f?.marks_obtained || 0),
        0
      );
      const max_score = questions.reduce((sum, q) => sum + (q.marks || 0), 0);
      const completion_date = new Date().toISOString();
      const topics = [...new Set(questions.map((q) => q.topic))];

      const formattedPaper = {
        metadata: {
          title,
          completion_date,
          total_score,
          max_score,
          topics,
          question_count: questions.length,
        },
        questions: questions.map((q, idx) => ({
          id: q.id || `q${idx + 1}`,
          question_latex: q.question_latex,
          correct_answer_latex: q.correct_answer_latex,
          explanation_latex: q.explanation_latex,
          marks: q.marks,
          topic: q.topic,
          user_answer: answers[idx] || "",
          feedback: feedback[idx] || {
            marks_obtained: 0,
            is_correct: false,
            comment: "Not attempted",
          },
        })),
      };

      const paperContent = JSON.stringify(formattedPaper, null, 2);

      const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
      const fileName = `${title.replace(
        /[^a-zA-Z0-9]/g,
        "_"
      )}_${timestamp}.json`;
      const filePath = `${user_id}/${fileName}`;
      const { error: uploadError } = await supabase.storage
        .from("solved-papers")
        .upload(
          filePath,
          new Blob([paperContent], { type: "application/json" })
        );

      if (uploadError) throw uploadError;

      const { data: paperRecord, error: dbError } = await supabase
        .from("completed_papers")
        .insert({
          user_id,
          title,
          file_path: filePath,
          total_score,
          max_score,
          completion_date,
          study_space_id: studySpaceId,
          paper_metadata: formattedPaper,
        })
        .select()
        .single();

      if (dbError) throw dbError;
      const paper_id = paperRecord.id;

      const answeredQuestions = questions.map((q, idx) => ({
        user_id,
        paper_id,
        question_no: idx + 1,
        topic: q.topic,
        marks_scored: feedback[idx]?.marks_obtained || 0,
        total_marks: q.marks,
        difficulty: q.difficulty || "Moderate",
        answered_at: new Date().toISOString(),
        study_space_id: studySpaceId,
        topic_cluster_id: q.topic_cluster_id || null,
        topic_cluster_name: q.topic_cluster_name || null,
        question_latex: q.question_latex,
        explanation_latex: q.explanation_latex,
      }));
      if (answeredQuestions.length > 0) {
        await supabase.from("answered_questions").insert(answeredQuestions);
      }

      await axios.post("http://localhost:9001/cluster-topics", {
        user_id,
        study_space_id: studySpaceId,
        h_q: 5,
        min_cluster_size: 2,
        min_samples: 1,
        clustering_method: "similarity",
        similarity_threshold: 0.7,
      });

      setPaperJSON(formattedPaper);
      setShowPreview(true);
    } catch (err) {
      alert("Failed to save practice paper.");
      console.error(err);
    }
  };

  const goPrev = () => setCurrent((prev) => Math.max(0, prev - 1));
  const goNext = () =>
    setCurrent((prev) => Math.min(questions.length - 1, prev + 1));

  const renderPreview = () => {
    return (
      <div className='max-w-4xl mx-auto bg-white p-8 rounded-xl shadow'>
        <h2 className='text-2xl font-bold mb-4'>{paperJSON.metadata.title}</h2>
        <p className='text-gray-600 mb-2'>
          Score: {paperJSON.metadata.total_score}/{paperJSON.metadata.max_score}
        </p>
        <p className='text-gray-600 mb-2'>
          Topics: {paperJSON.metadata.topics.join(", ")}
        </p>
        <p className='text-gray-600 mb-4'>
          Completed on:{" "}
          {new Date(paperJSON.metadata.completion_date).toLocaleString()}
        </p>
        <hr className='my-4' />
        {paperJSON.questions.map((q, idx) => (
          <div
            key={q.id}
            className='mb-8'
          >
            <h3 className='font-semibold text-xl mb-2'>Question {idx + 1}</h3>
            <div className='bg-gray-100 p-4 rounded text-lg mb-2'>
              <MathJax>{q.question_latex}</MathJax>
            </div>
            <div className='text-gray-700 mb-1'>
              <strong>Your Answer:</strong> {q.user_answer || "Not answered"}
            </div>
            <div className='text-gray-700 mb-1'>
              <strong>Marks:</strong> {q.feedback.marks_obtained} / {q.marks}
            </div>
            <div className='text-gray-700 mb-1'>
              <strong>Feedback:</strong> {q.feedback.comment}
            </div>
            <div className='text-green-800 mt-2'>
              <strong>Correct Answer:</strong>
              <div className='bg-green-100 p-2 rounded'>
                <MathJax>{q.correct_answer_latex}</MathJax>
              </div>
            </div>
            <div className='text-blue-800 mt-2'>
              <strong>Explanation:</strong>
              <div className='bg-blue-100 p-2 rounded'>
                <MathJax>{q.explanation_latex}</MathJax>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className='min-h-screen p-8 bg-gray-50'>
      {showPreview ? (
        renderPreview()
      ) : (
        <div className='flex flex-1 items-stretch py-12'>
          <div className='bg-white rounded-2xl shadow-xl p-10 w-full h-fit'>
            <h2 className='text-3xl font-bold text-gray-900 mb-1'>
              Create Questions
            </h2>
            <p className='text-gray-500 mb-6'>
              Tell us what you need and we'll generate perfect questions
            </p>
            {questions.length === 0 && (
              <form onSubmit={handleGenerate}>
                <div className='relative mb-8'>
                  <textarea
                    // ref={answerRef}
                    className='w-full border border-gray-200 rounded-lg p-4 pr-10 focus:outline-none focus:ring-2 focus:ring-blue-200 text-lg'
                    placeholder='Describe what you want to practice — include subjects, exams, or concepts to help us generate better exam-style questions. You can also upload reference files (PDFs, images).'
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    rows={5}
                  />
                  {/* <MathTextarea
                    textareaRef={answerRef}
                    value={answers[current] || ""}
                    onChange={(e) =>
                      handleAnswerChange(current, e.target.value)
                    }
                    placeholder="Enter your answer here..."
                  /> */}
                  <button
                    type='button'
                    className='absolute bottom-4 right-4 text-blue-600 text-2xl bg-transparent hover:bg-blue-100 rounded-full w-8 h-8 flex items-center justify-center'
                    onClick={() => setShowResourceMenu((v) => !v)}
                    aria-label='Add resources'
                  >
                    <svg
                      width='24'
                      height='24'
                      fill='none'
                      stroke='currentColor'
                      strokeWidth='3'
                      strokeLinecap='round'
                      strokeLinejoin='round'
                    >
                      <line
                        x1='12'
                        y1='5'
                        x2='12'
                        y2='19'
                      />
                      <line
                        x1='5'
                        y1='12'
                        x2='19'
                        y2='12'
                      />
                    </svg>
                  </button>
                  {showResourceMenu && (
                    <div className='absolute z-10 right-0 mt-2 w-72 bg-white rounded-xl shadow-xl border p-6'>
                      <div className='text-2xl font-semibold text-gray-700 mb-4'>
                        Add resources
                      </div>
                      <button
                        type='button'
                        className='flex items-center w-full px-2 py-3 rounded hover:bg-gray-100 text-left text-lg'
                      >
                        <span className='mr-3 text-2xl'>📁</span> From Files
                      </button>
                      <button
                        type='button'
                        className='flex items-center w-full px-2 py-3 rounded hover:bg-gray-100 text-left text-lg'
                        onClick={handleFileUpload}
                      >
                        <span className='mr-3 text-2xl'>⬆️</span> From computer
                      </button>
                    </div>
                  )}
                  <input
                    type='file'
                    accept='.pdf,image/*'
                    ref={fileInputRef}
                    onChange={handleFileChange}
                    className='hidden'
                  />
                </div>
                <div className='flex items-center gap-8 mb-8'>
                  <div className='flex items-center gap-2'>
                    <span className='font-medium text-gray-700 text-lg'>
                      Type:
                    </span>
                    <select
                      className='border rounded px-4 py-2 text-lg'
                      value={type}
                      onChange={(e) => setType(e.target.value)}
                      required
                    >
                      <option value=''>Select types</option>
                      <option value='MCQ'>MCQ</option>
                      <option value='Short Answer'>Short Answer</option>
                      <option value='Long Answer'>Long Answer</option>
                    </select>
                  </div>
                  <div className='flex items-center gap-2'>
                    <span className='font-medium text-gray-700 text-lg'>
                      Difficulty:
                    </span>
                    <select
                      className='border rounded px-4 py-2 text-lg'
                      value={difficulty}
                      onChange={(e) => setDifficulty(e.target.value)}
                      required
                    >
                      <option value=''>Select difficulty</option>
                      <option value='Easy'>Easy</option>
                      <option value='Medium'>Moderate</option>
                      <option value='Hard'>Hard</option>
                    </select>
                  </div>
                  <div className='flex items-center gap-2'>
                    <span className='font-medium text-gray-700 text-lg'>
                      Number of questions:
                    </span>
                    <input
                      type='number'
                      onChange={(e) => setNumQuestions(e.target.value)}
                      min={1}
                      max={10}
                      value={numQuestions}
                      className='w-14 border rounded px-3 py-2 text-lg'
                    />
                  </div>
                </div>
                <button
                  type='submit'
                  className='bg-[#2563EB] text-white px-8 py-3 rounded-lg font-semibold text-lg hover:bg-blue-700 transition w-full mt-4'
                  disabled={loading}
                >
                  {loading ? "Generating..." : "Create Questions"}
                </button>
              </form>
            )}

            {/* Single-question view */}
            {questions && questions.length > 0 && (
              <div className='mt-10 max-w-4xl mx-auto bg-white rounded-2xl shadow p-8'>
                <div className='flex justify-between items-center mb-6'>
                  <div className='text-3xl font-bold'>
                    Question {current + 1} of {questions.length}
                  </div>
                  <div className='text-xl text-gray-500 font-semibold'>
                    Marks: {questions[current].marks}
                  </div>
                </div>
                <div className='bg-gray-50 rounded-lg p-6 text-xl mb-6'>
                  <MathJax>{questions[current].question_latex}</MathJax>
                </div>
                <hr className='mb-6' />
                <div className='mb-2 font-semibold text-lg'>Your Answer:</div>
                <button
                  type='button'
                  className='mt-2 text-sm text-blue-600 hover:underline'
                  onClick={() => setShowToolbar((prev) => !prev)}
                >
                  {showToolbar ? "Hide Math Toolbar" : "Show Math Toolbar"}
                </button>
                {/* <textarea
                  ref={answerRef}
                  className="w-full border border-gray-300 rounded-lg p-4 text-lg mb-6"
                  rows={4}
                  placeholder="Enter your answer here..."
                  value={answers[current] || ""}
                  onChange={(e) => handleAnswerChange(current, e.target.value)}
                /> */}
                <MathTextarea
                  textareaRef={answerRef}
                  value={answers[current] || ""}
                  onChange={(e) => handleAnswerChange(current, e.target.value)}
                  placeholder='Enter your answer here...'
                />

                <div className='flex justify-between items-center mt-6'>
                  <button
                    className='px-6 py-2 rounded bg-gray-100 text-gray-700 font-semibold border flex items-center'
                    onClick={goPrev}
                    disabled={current === 0}
                  >
                    &#8592; Previous
                  </button>
                  <div className='text-gray-500'>
                    Question {current + 1} of {questions.length}
                  </div>
                  <button
                    className='px-6 py-2 rounded bg-gray-100 text-gray-700 font-semibold border flex items-center'
                    onClick={goNext}
                    disabled={current === questions.length - 1}
                  >
                    Next &#8594;
                  </button>
                </div>
                <div className='flex justify-end mt-6'>
                  {!feedback[current] ? (
                    <button
                      className='px-8 py-3 rounded bg-blue-400 text-white font-semibold text-lg flex items-center gap-2'
                      onClick={() =>
                        handleCheckAnswer(current, questions[current])
                      }
                    >
                      <span>&#10003;</span> Submit Answer
                    </button>
                  ) : (
                    <div className='flex gap-4'>
                      <button
                        className='px-6 py-2 rounded bg-red-400 text-black font-semibold flex items-center gap-2'
                        onClick={async () => {
                          setRechecking(true);
                          try {
                            await handleCheckAnswer(
                              current,
                              questions[current]
                            );
                            setToast("Recheck completed.");
                          } catch (err) {
                            setToast("Failed to recheck.");
                          } finally {
                            setRechecking(false);
                          }
                        }}
                        disabled={rechecking}
                      >
                        {rechecking ? <>⏳ Rechecking...</> : "Request Recheck"}
                      </button>

                      <button
                        className='px-6 py-2 rounded bg-blue-600 text-white font-semibold'
                        onClick={handleAskAI}
                      >
                        Ask AI
                      </button>
                    </div>
                  )}
                </div>

                {feedback[current] && (
                  <div className='mt-8 space-y-6'>
                    {/* Feedback */}
                    <div className='bg-red-100 border border-red-200 rounded-xl p-6'>
                      <div className='font-bold text-lg text-red-700 mb-2'>
                        Feedback:
                      </div>
                      <div className='text-red-700 mb-2'>
                        {feedback[current].comment}
                      </div>
                      <div className='font-semibold text-red-800'>
                        Marks:{" "}
                        {feedback[current].marks_obtained ??
                          feedback[current].marks ??
                          0}
                        /{questions[current].marks}
                      </div>
                    </div>
                    {/* Correct Answer */}
                    <div className='bg-green-100 border border-green-200 rounded-xl p-6'>
                      <div className='font-bold text-lg text-green-800 mb-2'>
                        Correct Answer:
                      </div>
                      <div className='text-green-900 text-xl'>
                        <MathJax>
                          {questions[current].correct_answer_latex}
                        </MathJax>
                      </div>
                    </div>
                    {/* Explanation */}
                    <div className='bg-blue-100 border border-blue-200 rounded-xl p-6'>
                      <div className='font-bold text-lg text-blue-800 mb-2'>
                        Explanation:
                      </div>
                      <div className='text-blue-700'>
                        <MathJax>
                          {questions[current].explanation_latex}
                        </MathJax>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
            {current === questions.length - 1 && (
              <div className='flex justify-end mt-8'>
                <button
                  className='px-8 py-3 rounded bg-green-500 text-white font-semibold text-lg flex items-center gap-2'
                  onClick={handleCompletePractice}
                >
                  <span>&#10003;</span> Complete Practice
                </button>
              </div>
            )}
          </div>
          <AskAIDrawer
            isOpen={showAskAIDrawer}
            onClose={() => setShowAskAIDrawer(false)}
            questionData={{
              question_latex: questions[current]?.question_latex,
              correct_answer_latex: questions[current]?.correct_answer_latex,
              explanation_latex: questions[current]?.explanation_latex,
              marks: questions[current]?.marks,
              topic: questions[current]?.topic,
              student_answer: answers[current] || "",
              comment: feedback[current]?.comment || "",
            }}
          />
          {toast && (
            <Toast
              message={toast}
              onClose={() => setToast(null)}
            />
          )}
        </div>
      )}
      {showToolbar && !showPreview && (
        <MathInputToolbar targetRef={answerRef} />
      )}
    </div>
  );
}

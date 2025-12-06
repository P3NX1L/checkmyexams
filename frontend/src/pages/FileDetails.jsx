import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { supabase } from "../supabaseClient";
import { MathJax, MathJaxContext } from "better-react-mathjax";

export default function FileDetails() {
  const { paperId } = useParams();
  const [paper, setPaper] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPaper = async () => {
      const { data, error } = await supabase
        .from("completed_papers")
        .select("*")
        .eq("id", paperId)
        .single();

      if (error) {
        console.error("Error loading paper:", error);
      } else {
        setPaper(data);
      }

      setLoading(false);
    };

    fetchPaper();
  }, [paperId]);

  if (loading) return <div className='p-10 text-center'>Loading...</div>;

  if (!paper || !paper.paper_metadata)
    return <div className='p-10 text-red-500'>Paper not found.</div>;

  const paperJSON = paper.paper_metadata;

  return (
    <MathJaxContext>
      <div className='min-h-screen bg-gray-50 p-8'>
        <div className='max-w-4xl mx-auto bg-white p-8 rounded-xl shadow'>
          <h2 className='text-2xl font-bold mb-4'>
            {paperJSON.metadata.title}
          </h2>
          <p className='text-gray-600 mb-2'>
            Score: {paperJSON.metadata.total_score}/
            {paperJSON.metadata.max_score}
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
      </div>
    </MathJaxContext>
  );
}

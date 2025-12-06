import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { supabase } from "../supabaseClient";

export default function Files() {
  const [papers, setPapers] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchPapers = async () => {
      const userId = localStorage.getItem("user_id");
      const studySpaceId = localStorage.getItem("study_space_id");

      if (!userId || !studySpaceId) {
        console.warn("Missing user or study space ID");
        return;
      }

      const { data, error } = await supabase
        .from("completed_papers")
        .select("*")
        .eq("user_id", userId)
        .eq("study_space_id", studySpaceId)
        .order("completion_date", { ascending: false });

      if (error) {
        console.error("Error fetching papers:", error);
        return;
      }

      setPapers(data || []);
    };

    fetchPapers();
  }, []);

  const handleView = (paperId) => {
    navigate(`/dashboard/files/${paperId}`);
  };

  const handleDownload = async (paperId) => {
    const paper = papers.find((p) => p.id === paperId);
    if (!paper || !paper.paper_metadata) return;

    const { metadata, questions } = paper.paper_metadata;

    const htmlContent = `
      <!DOCTYPE html>
      <html>
        <head>
          <meta charset="UTF-8" />
          <title>${metadata.title || "Practice Paper"}</title>
          <style>
            body { font-family: sans-serif; padding: 30px; background: #f9f9f9; color: #333; }
            h1 { color: #1e3a8a; }
            h2 { color: #2563eb; margin-top: 40px; }
            .question { margin-bottom: 30px; padding: 20px; background: white; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .latex-block { background: #f3f4f6; padding: 10px; border-radius: 6px; margin: 10px 0; }
            .section-title { font-weight: bold; margin-top: 10px; color: #111827; }
          </style>
        </head>
        <body>
          <h1>${metadata.title}</h1>
          <p><strong>Score:</strong> ${metadata.total_score} / ${
      metadata.max_score
    }</p>
          <p><strong>Topics:</strong> ${metadata.topics.join(", ")}</p>
          <p><strong>Completed on:</strong> ${new Date(
            metadata.completion_date
          ).toLocaleString()}</p>
          <hr />

          ${questions
            .map(
              (q, idx) => `
            <div class="question">
              <h2>Question ${idx + 1}</h2>
              <div class="latex-block">${q.question_latex}</div>
              <div class="section-title">Your Answer:</div>
              <div>${q.user_answer || "Not answered"}</div>
              <div class="section-title">Marks:</div>
              <div>${q.feedback?.marks_obtained || 0} / ${q.marks}</div>
              <div class="section-title">Feedback:</div>
              <div>${q.feedback?.comment || "No feedback"}</div>
              <div class="section-title">Correct Answer:</div>
              <div class="latex-block">${q.correct_answer_latex}</div>
              <div class="section-title">Explanation:</div>
              <div class="latex-block">${q.explanation_latex}</div>
            </div>
          `
            )
            .join("")}
        </body>
      </html>
    `;

    const blob = new Blob([htmlContent], { type: "text/html" });
    const downloadUrl = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = downloadUrl;
    link.download = `${
      metadata.title.replace(/\s+/g, "_") || "practice-paper"
    }_${paperId}.html`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(downloadUrl);
  };

  return (
    <div className='p-10'>
      <h1 className='text-3xl font-bold mb-6'>Files</h1>
      <p className='mb-8 text-gray-500'>
        Completed papers and practice sessions for this study space
      </p>
      {papers.length === 0 ? (
        <div className='text-gray-400'>No files found.</div>
      ) : (
        <div className='space-y-6'>
          {papers.map((paper) => (
            <div
              key={paper.id}
              className='border rounded-xl p-6 flex items-center justify-between bg-white shadow'
            >
              <div>
                <div className='font-bold text-lg mb-2'>
                  {paper.title || `Practice Paper - ${paper.completedAt}`}
                </div>
                <div className='text-gray-500 text-sm mb-1'>
                  {new Date(paper.completedAt).toLocaleString()}
                </div>
                <div className='text-sm text-gray-400 mt-1'>
                  {paper.paper_metadata?.questions?.length || 0} questions
                </div>
              </div>
              <div className='flex gap-3 items-center'>
                <button
                  className='px-4 py-2 rounded bg-blue-100 text-blue-700 font-semibold'
                  onClick={() => handleView(paper.id)}
                >
                  View
                </button>
                <button
                  className='px-4 py-2 rounded bg-gray-100 text-gray-700 font-semibold'
                  onClick={() => handleDownload(paper.id)}
                >
                  Download
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { supabase } from "../supabaseClient";

const Analytics = () => {
  const [clusters, setClusters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isHeatmapView, setIsHeatmapView] = useState(false);
  const userId = localStorage.getItem("user_id");
  const studySpaceId = localStorage.getItem("study_space_id");
  const navigate = useNavigate();

  useEffect(() => {
    const fetchAnalytics = async () => {
      if (!userId || !studySpaceId) return;

      try {
        const { data, error } = await supabase
          .from("topic_cluster_accuracy")
          .select("*")
          .eq("user_id", userId)
          .eq("study_space_id", studySpaceId);

        if (error) {
          console.error("Supabase error fetching analytics:", error);
        } else {
          setClusters(data || []);
        }
      } catch (err) {
        console.error("Unexpected error fetching analytics:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, [userId, studySpaceId]);

  const handlePracticeMore = (clusterId, clusterName) => {
    navigate("/create-questions", {
      state: {
        topic_cluster_id: clusterId,
        topic_cluster_name: clusterName,
      },
    });
  };

  const weakTopics = clusters.filter((c) => c.accuracy < 0.6);
  const moderateTopics = clusters.filter(
    (c) => c.accuracy >= 0.6 && c.accuracy < 0.8
  );
  const strongTopics = clusters.filter((c) => c.accuracy >= 0.8);

  const renderCard = (topic) => (
    <div
      key={topic.topic_cluster_id}
      className='rounded-xl bg-white p-4 shadow border mb-4'
    >
      <h3 className='font-semibold text-md'>{topic.topic_cluster_name}</h3>
      <div className='text-sm flex gap-3 mt-1'>
        {topic.easy_no > 0 && (
          <span className='bg-gray-200 text-gray-700 px-2 py-0.5 rounded text-xs'>
            E:{topic.easy_no}
          </span>
        )}
        {topic.moderate_no > 0 && (
          <span className='bg-gray-200 text-gray-700 px-2 py-0.5 rounded text-xs'>
            M:{topic.moderate_no}
          </span>
        )}
        {topic.hard_no > 0 && (
          <span className='bg-gray-200 text-gray-700 px-2 py-0.5 rounded text-xs'>
            H:{topic.hard_no}
          </span>
        )}
      </div>
      <div className='text-right font-bold mt-2 text-sm'>
        {(topic.accuracy * 100).toFixed(0)}%
      </div>
      <div className='w-full h-2 bg-gray-200 rounded mt-1'>
        <div
          className={`h-2 rounded ${
            topic.accuracy >= 0.8
              ? "bg-green-500"
              : topic.accuracy >= 0.6
              ? "bg-yellow-500"
              : "bg-red-500"
          }`}
          style={{ width: `${topic.accuracy * 100}%` }}
        ></div>
      </div>
      <button
        onClick={() =>
          handlePracticeMore(topic.topic_cluster_id, topic.topic_cluster_name)
        }
        className='mt-3 w-full text-sm bg-gray-100 hover:shadow font-medium py-1 rounded flex justify-center items-center gap-2'
      >
        📖 Practice More
      </button>
    </div>
  );

  const renderColumn = (title, topics, color = "text-gray-700") => (
    <div className='w-full sm:w-1/3 p-2'>
      <div className='bg-white rounded-xl shadow p-4 h-full'>
        <h2 className={`text-lg font-bold mb-3 ${color}`}>{title}</h2>
        {topics.length === 0 ? (
          <div className='text-center text-sm text-gray-400 py-6'>
            No topics in progress.
          </div>
        ) : (
          topics.map(renderCard)
        )}
      </div>
    </div>
  );

  const renderListView = () => (
    <div className='flex flex-wrap -mx-2'>
      {renderColumn("🔻 Need Focus", weakTopics, "text-red-600")}
      {renderColumn("🎯 Improving", moderateTopics, "text-orange-500")}
      {renderColumn("📈 Strong", strongTopics, "text-green-600")}
    </div>
  );

  const renderHeatmap = () => (
    <div className='grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4'>
      {clusters.map((topic) => (
        <div
          key={topic.topic_cluster_id}
          className={`rounded p-4 text-white shadow text-sm ${
            topic.accuracy >= 0.8
              ? "bg-green-500"
              : topic.accuracy >= 0.6
              ? "bg-yellow-500"
              : "bg-red-500"
          }`}
        >
          <h3 className='font-semibold mb-1'>{topic.topic_cluster_name}</h3>
          <p>Accuracy: {(topic.accuracy * 100).toFixed(1)}%</p>
          <p>
            E: {topic.easy_no} • M: {topic.moderate_no} • H: {topic.hard_no}
          </p>
          <button
            onClick={() =>
              handlePracticeMore(
                topic.topic_cluster_id,
                topic.topic_cluster_name
              )
            }
            className='mt-2 underline text-white text-sm'
          >
            Practice More
          </button>
        </div>
      ))}
    </div>
  );

  if (loading)
    return <div className='text-center py-10'>Loading analytics...</div>;

  return (
    <div className='max-w-7xl mx-auto px-4 py-8'>
      <div className='flex justify-between items-center mb-6'>
        <div>
          <h1 className='text-2xl font-bold flex items-center gap-2'>
            📊 Analytics
          </h1>
          <p className='text-sm text-gray-500'>Study performance overview</p>
        </div>
        <button
          onClick={() => setIsHeatmapView((prev) => !prev)}
          className='bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded shadow text-sm'
        >
          {isHeatmapView ? "📋 List View" : "🔳 Heatmap"}
        </button>
      </div>
      {clusters.length === 0 ? (
        <p className='text-gray-600 text-center mt-10'>
          No data available. Start answering questions!
        </p>
      ) : isHeatmapView ? (
        renderHeatmap()
      ) : (
        renderListView()
      )}
    </div>
  );
};

export default Analytics;

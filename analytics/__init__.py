# ANALYTICS

'''
1. STUDENT ANSWERS A QUESTION -> HITS THE ANALYTICS TRIGGER
2. BACKEND UPDATES THE ANALYTICS ROW IN SUPABASE (TABLE "ANALYTICS") 
3. immediately after updating -> backend again fetches the table row and create analytics_history_log to transform analytics history row
4. analytics_history.repository.save_history_event() inserts those rows into multiple tables in Supabase: {5 tables of history}
5. seperately llm_feedback_summary creates strengths/weakness. [the prompt is needed to be changed]

'''
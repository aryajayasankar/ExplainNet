export type AnalysisStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface Topic {
  id: number;
  topic_name: string;
  analysis_status: AnalysisStatus;
  total_videos: number;
  total_articles: number;
  videos_found: number;
  articles_found: number;
  overall_sentiment: string;
  overall_impact_score: number;
  created_at: string;
  last_analyzed_at?: string;
  error_message?: string;
  unique_sources_count?: number;
  processing_time_seconds?: number;
}

export interface TopicCreate {
  topic_name: string;
}

export interface Video {
  id: number;
  topic_id: number;
  video_id: string;
  title: string;
  description?: string;
  channel_title: string;
  channel_id: string;
  published_at: string;
  thumbnail_url?: string;
  view_count: number;
  like_count: number;
  comment_count: number;
  duration?: string;
  subscriber_count?: number;
  impact_score?: number;
  reach_score?: number;
  engagement_score?: number;
  sentiment_score?: number;
  quality_score?: number;
  influence_score?: number;
  recency_boost?: number;
  overall_sentiment?: string;
  confidence_score?: number;
  emotions_json?: string;
  created_at: string;
}

export interface Sentiment {
  id: number;
  video_id: number;
  model_name: string; // 'huggingface' | 'gemini'
  sentiment: string;
  confidence?: number;
  positive_score?: number;
  negative_score?: number;
  neutral_score?: number;
  emotional_tone?: string;
  objectivity_score?: number;
  bias_level?: string;
  bias_type?: string;
  controversy_level?: string;
  evidence_quality?: string;
  key_themes?: string;
  neutral_summary?: string;
  created_at: string;
  // Justifications returned by models
  hf_justification?: string;
  gemini_justification?: string;
  gemini_sarcasm_score?: number;
  emotions_json?: string;
}

export interface Comment {
  id: number;
  video_id: number;
  comment_id: string;
  author: string;
  text: string;
  like_count: number;
  published_at: string;
  sentiment?: string;
  toxicity_score?: number;
  hf_sentiment?: string;
  hf_score?: number;
  hf_justification?: string;
  gemini_sentiment?: string;
  gemini_support?: string;
  gemini_score?: number;
  gemini_justification?: string;
  gemini_sarcasm_score?: number;
  gemini_emotions_json?: string;
  created_at: string;
}

export interface Transcript {
  id: number;
  video_id: number;
  text: string;
  language?: string;
  confidence?: number;
  word_count?: number;
  processing_time?: number;
  has_speech?: boolean;
  created_at: string;
}

export interface NewsArticle {
  id: number;
  topic_id: number;
  title: string;
  description?: string;
  url: string;
  source: string;
  source_type?: string;
  author?: string;
  published_at: string;
  content?: string;
  hf_sentiment?: string;
  hf_score?: number;
  gemini_sentiment?: string;
  gemini_support?: string;
  gemini_score?: number;
  gemini_justification?: string;
  gemini_sarcasm_score?: number;
  hf_justification?: string;
  impact_score?: number;
  entities_json?: string;
  relevance_score?: number;
  created_at: string;
}

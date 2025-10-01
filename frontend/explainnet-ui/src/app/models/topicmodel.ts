export interface Topic {
    topic_id: number;
    topic_name: string;
    article_count: number;
    video_count: number;
    created_at?: string;
    updated_at?: string;
}
export interface AuthSession {
  username: string;
  displayName: string;
  token: string;
  isGuest: boolean;
}

export interface Challenge {
  date: string;
  weekday: string;
  object_name: string;
  object_emoji: string;
  difficulty: 'easy' | 'medium' | 'hard';
  base_points: number;
  hint?: string;
  already_done: boolean;
}

export interface WeekDay {
  date: string;
  weekday: string;
  object_name: string;
  object_emoji: string;
  difficulty: 'easy' | 'medium' | 'hard';
  is_today: boolean;
}

export interface ScoreResult {
  correct: boolean;
  detected_class: string;
  confidence_pct: number;
  total_score: number;
  base_score: number;
  speed_bonus: number;
  framing_bonus: number;
  clutter_penalty: number;
  attempt_penalty: number;
  speed_label: string;
  framing_label: string;
  difficulty_mult: number;
  attempt_number: number;
  seconds_elapsed: number;
  annotated_image_b64?: string;
}

export interface FeedEntry {
  submission_id: number;
  username: string;
  display_name: string;
  object_emoji: string;
  object_name: string;
  total_score: number;
  confidence_pct: number;
  speed_label: string;
  framing_label: string;
  correct: boolean;
  submitted_at: string;
  annotated_image_b64?: string;
  like_count: number;
  comment_count: number;
  user_liked: boolean;
}

export interface LeaderboardEntry {
  rank: number;
  username: string;
  display_name: string;
  total_score: number;
  current_streak: number;
}

export interface FriendInfo {
  username: string;
  display_name: string;
  total_score: number;
  current_streak: number;
  status: 'accepted' | 'pending_sent' | 'pending_received' | 'none';
}

export interface FriendRequest {
  friendship_id: number;
  username: string;
  display_name: string;
  created_at: string;
}

export interface Comment {
  id: number;
  username: string;
  display_name: string;
  text: string;
  created_at: string;
}

export interface UserStats {
  username: string;
  display_name: string;
  total_score: number;
  current_streak: number;
  max_streak: number;
}

import { API_URL } from './config';
import {
  Challenge, ScoreResult, FeedEntry, LeaderboardEntry,
  FriendInfo, FriendRequest, Comment, UserStats, WeekDay,
} from './types';

function authHeaders(token?: string): Record<string, string> {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string,
): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { ...authHeaders(token), ...options.headers },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || `Error ${res.status}`);
  return data as T;
}

// ── Auth ─────────────────────────────────────────────────────────────────────

export const apiRegister = (body: {
  username: string; display_name: string; email: string; password: string;
}) => request<any>('/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
});

export const apiLogin = (email: string, password: string) =>
  request<any>('/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });

export const apiGuest = (username: string, display_name: string) =>
  request<any>(`/guest?username=${encodeURIComponent(username)}&display_name=${encodeURIComponent(display_name)}`, {
    method: 'POST',
  });

export const apiMe = (token: string) =>
  request<UserStats>('/me', {}, token);

export const apiUpdateProfile = (display_name: string, token: string) =>
  request<UserStats>(`/me/profile?display_name=${encodeURIComponent(display_name)}`, {
    method: 'PATCH',
  }, token);

// ── Challenge ────────────────────────────────────────────────────────────────

export const apiToday = (token?: string) =>
  request<Challenge>('/today', {}, token);

export const apiWeek = () =>
  request<{ week: WeekDay[] }>('/week');

// ── Submit ───────────────────────────────────────────────────────────────────

export async function apiSubmit(params: {
  username: string;
  displayName: string;
  secondsSinceNotif: number;
  attemptNumber: number;
  photoUri: string;
  token?: string;
}): Promise<ScoreResult> {
  const formData = new FormData();
  formData.append('username', params.username);
  formData.append('display_name', params.displayName);
  formData.append('seconds_since_notification', String(params.secondsSinceNotif));
  formData.append('attempt_number', String(params.attemptNumber));
  formData.append('photo', { uri: params.photoUri, type: 'image/jpeg', name: 'snap.jpg' } as any);

  const res = await fetch(`${API_URL}/submit`, {
    method: 'POST',
    headers: params.token ? { Authorization: `Bearer ${params.token}` } : {},
    body: formData,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || `Error ${res.status}`);
  return data as ScoreResult;
}

// ── Feed ─────────────────────────────────────────────────────────────────────

export const apiFeed = (friendsOnly: boolean, token?: string) =>
  request<{ date: string; entries: FeedEntry[] }>(
    friendsOnly ? '/feed?friends_only=true' : '/feed',
    {}, token,
  );

// ── Leaderboard ──────────────────────────────────────────────────────────────

export const apiLeaderboard = (limit = 20) =>
  request<{ entries: LeaderboardEntry[] }>(`/leaderboard?limit=${limit}`);

// ── Friends ──────────────────────────────────────────────────────────────────

export const apiFriends = (token: string) =>
  request<{ friends: FriendInfo[]; pending_received: FriendRequest[]; pending_sent: FriendInfo[] }>(
    '/friends', {}, token,
  );

export const apiSearchUsers = (q: string, token: string) =>
  request<FriendInfo[]>(`/friends/search?q=${encodeURIComponent(q)}`, {}, token);

export const apiAddFriend = (username: string, token: string) =>
  request<any>(`/friends/${username}`, { method: 'POST' }, token);

export const apiAcceptFriend = (username: string, token: string) =>
  request<any>(`/friends/${username}/accept`, { method: 'POST' }, token);

export const apiRemoveFriend = (username: string, token: string) =>
  request<any>(`/friends/${username}`, { method: 'DELETE' }, token);

// ── Likes & Comentarios ──────────────────────────────────────────────────────

export const apiLike = (sid: number, token: string) =>
  request<{ likes: number }>(`/submission/${sid}/like`, { method: 'POST' }, token);

export const apiUnlike = (sid: number, token: string) =>
  request<{ likes: number }>(`/submission/${sid}/like`, { method: 'DELETE' }, token);

export const apiComments = (sid: number, token?: string) =>
  request<Comment[]>(`/submission/${sid}/comments`, {}, token);

export const apiPostComment = (sid: number, text: string, token: string) =>
  request<Comment>(`/submission/${sid}/comments`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  }, token);

// ── History ──────────────────────────────────────────────────────────────────

export const apiHistory = (username: string, token?: string) =>
  request<any>(`/user/${username}/history`, {}, token);

import AsyncStorage from '@react-native-async-storage/async-storage';
import { AuthSession } from './types';

const KEYS = {
  username:    'snapit_username',
  displayName: 'snapit_displayname',
  token:       'snapit_token',
  isGuest:     'snapit_is_guest',
  notifEpoch:  'snapit_notif_epoch',
  scoreToday:  'snapit_score_today',
};

export async function saveSession(data: {
  username: string;
  display_name: string;
  access_token: string;
  is_guest: boolean;
}): Promise<AuthSession> {
  await AsyncStorage.multiSet([
    [KEYS.username,    data.username],
    [KEYS.displayName, data.display_name],
    [KEYS.token,       data.access_token],
    [KEYS.isGuest,     String(data.is_guest)],
  ]);
  return {
    username:    data.username,
    displayName: data.display_name,
    token:       data.access_token,
    isGuest:     data.is_guest,
  };
}

export async function loadSession(): Promise<AuthSession | null> {
  const values = await AsyncStorage.multiGet([
    KEYS.username, KEYS.displayName, KEYS.token, KEYS.isGuest,
  ]);
  const username    = values[0][1];
  const displayName = values[1][1];
  const token       = values[2][1];
  const isGuest     = values[3][1] === 'true';
  if (!username || !token) return null;
  return { username, displayName: displayName || username, token, isGuest };
}

export async function clearSession(): Promise<void> {
  await AsyncStorage.multiRemove(Object.values(KEYS));
}

export async function saveScoreToday(score: number): Promise<void> {
  await AsyncStorage.setItem(KEYS.scoreToday, String(score));
}

export async function getScoreToday(): Promise<number | null> {
  const v = await AsyncStorage.getItem(KEYS.scoreToday);
  return v ? Number(v) : null;
}

export async function saveNotifEpoch(epoch: number): Promise<void> {
  await AsyncStorage.setItem(KEYS.notifEpoch, String(epoch));
}

export async function getNotifEpoch(): Promise<number | null> {
  const v = await AsyncStorage.getItem(KEYS.notifEpoch);
  return v ? Number(v) : null;
}

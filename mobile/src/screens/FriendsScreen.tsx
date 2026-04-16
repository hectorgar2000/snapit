import React, { useState, useCallback } from 'react';
import {
  View, Text, FlatList, TouchableOpacity, StyleSheet,
  TextInput, ActivityIndicator, Alert,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { useTranslation } from 'react-i18next';
import { C, S } from '../theme';
import { apiFriends, apiSearchUsers, apiAddFriend, apiAcceptFriend, apiRemoveFriend } from '../api';
import { FriendInfo, FriendRequest, AuthSession } from '../types';

interface Props { session: AuthSession }

export default function FriendsScreen({ session }: Props) {
  const { t } = useTranslation();

  const [friends,       setFriends]       = useState<FriendInfo[]>([]);
  const [received,      setReceived]      = useState<FriendRequest[]>([]);
  const [loading,       setLoading]       = useState(true);
  const [searchQuery,   setSearchQuery]   = useState('');
  const [searchResults, setSearchResults] = useState<FriendInfo[]>([]);
  const [searching,     setSearching]     = useState(false);
  const searchTimer = React.useRef<ReturnType<typeof setTimeout> | null>(null);

  useFocusEffect(useCallback(() => { loadFriends(); }, []));

  if (session.isGuest) return (
    <View style={styles.guestState}>
      <Text style={styles.guestTitle}>{t('friends.title')}</Text>
      <Text style={[S.muted, { textAlign: 'center', marginBottom: 20 }]}>{t('friends.guestBody')}</Text>
    </View>
  );

  async function loadFriends() {
    setLoading(true);
    try {
      const data = await apiFriends(session.token);
      setFriends(data.friends);
      setReceived(data.pending_received);
    } catch {
      Alert.alert(t('common.error'), t('friends.loadError'));
    } finally {
      setLoading(false);
    }
  }

  function onSearchChange(text: string) {
    setSearchQuery(text);
    if (searchTimer.current) clearTimeout(searchTimer.current);
    if (text.length < 3) { setSearchResults([]); return; }
    searchTimer.current = setTimeout(async () => {
      setSearching(true);
      try {
        setSearchResults(await apiSearchUsers(text, session.token));
      } catch {} finally { setSearching(false); }
    }, 400);
  }

  async function addFriend(username: string) {
    try {
      await apiAddFriend(username, session.token);
      setSearchResults(prev => prev.map(u =>
        u.username === username ? { ...u, status: 'pending_sent' } : u
      ));
    } catch (e: any) { Alert.alert(t('common.error'), e.message); }
  }

  async function acceptFriend(username: string) {
    try { await apiAcceptFriend(username, session.token); loadFriends(); }
    catch (e: any) { Alert.alert(t('common.error'), e.message); }
  }

  async function removeFriend(username: string) {
    Alert.alert(t('friends.removeTitle'), t('friends.removeBody', { username }), [
      { text: t('common.cancel'), style: 'cancel' },
      { text: t('common.delete'), style: 'destructive', onPress: async () => {
        try { await apiRemoveFriend(username, session.token); loadFriends(); }
        catch (e: any) { Alert.alert(t('common.error'), e.message); }
      }},
    ]);
  }

  const ActionBtn = ({ user }: { user: FriendInfo }) => {
    if (user.status === 'accepted')
      return <View style={styles.btnPending}><Text style={styles.btnPendingText}>{t('friends.alreadyFriends')}</Text></View>;
    if (user.status === 'pending_sent')
      return <View style={styles.btnPending}><Text style={styles.btnPendingText}>⏳</Text></View>;
    if (user.status === 'pending_received')
      return (
        <TouchableOpacity style={styles.btnAccept} onPress={() => acceptFriend(user.username)}>
          <Text style={{ color: C.green, fontWeight: '700' }}>{t('friends.accept')}</Text>
        </TouchableOpacity>
      );
    return (
      <TouchableOpacity style={styles.btnAdd} onPress={() => addFriend(user.username)}>
        <Text style={{ color: C.accent, fontWeight: '700' }}>{t('friends.add')}</Text>
      </TouchableOpacity>
    );
  };

  return (
    <View style={{ flex: 1, backgroundColor: C.bg }}>
      <View style={{ padding: 16 }}>
        <View style={styles.searchRow}>
          <TextInput
            style={[S.input, { flex: 1, marginBottom: 0 }]}
            placeholder={t('friends.search')}
            placeholderTextColor={C.muted}
            value={searchQuery}
            onChangeText={onSearchChange}
          />
          {searching && <ActivityIndicator color={C.accent} style={{ marginLeft: 8 }} />}
        </View>
        {searchResults.map(u => (
          <View key={u.username} style={styles.friendRow}>
            <View style={styles.avatar}><Text style={styles.avatarText}>{u.display_name[0].toUpperCase()}</Text></View>
            <View style={{ flex: 1 }}>
              <Text style={styles.friendName}>{u.display_name}</Text>
              <Text style={S.muted}>@{u.username} · {u.total_score.toLocaleString()} pts</Text>
            </View>
            <ActionBtn user={u} />
          </View>
        ))}
      </View>

      {loading ? (
        <ActivityIndicator color={C.accent} style={{ marginTop: 20 }} />
      ) : (
        <FlatList
          data={[
            ...received.map(r => ({ type: 'request' as const, data: r })),
            ...friends.map(f  => ({ type: 'friend'  as const, data: f })),
          ]}
          keyExtractor={(item, i) => `${item.type}-${i}`}
          contentContainerStyle={{ paddingHorizontal: 16 }}
          ListHeaderComponent={received.length > 0
            ? <Text style={S.sectionTitle}>{t('friends.received')}</Text>
            : null}
          ListEmptyComponent={
            <Text style={[S.muted, { textAlign: 'center', marginTop: 20 }]}>{t('friends.empty')}</Text>
          }
          renderItem={({ item }) => {
            if (item.type === 'request') {
              const r = item.data as FriendRequest;
              return (
                <View style={styles.friendRow}>
                  <View style={styles.avatar}><Text style={styles.avatarText}>{r.display_name[0].toUpperCase()}</Text></View>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.friendName}>{r.display_name}</Text>
                    <Text style={S.muted}>@{r.username} · {t('friends.wantsFriend')}</Text>
                  </View>
                  <View style={{ flexDirection: 'row', gap: 6 }}>
                    <TouchableOpacity style={styles.btnAccept} onPress={() => acceptFriend(r.username)}>
                      <Text style={{ color: C.green, fontWeight: '700' }}>✓</Text>
                    </TouchableOpacity>
                    <TouchableOpacity style={styles.btnDecline} onPress={() => removeFriend(r.username)}>
                      <Text style={{ color: C.red, fontWeight: '700' }}>✕</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              );
            }
            const f = item.data as FriendInfo;
            return (
              <View style={styles.friendRow}>
                <View style={styles.avatar}><Text style={styles.avatarText}>{f.display_name[0].toUpperCase()}</Text></View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.friendName}>{f.display_name}</Text>
                  <Text style={S.muted}>@{f.username} · {t('friends.streakDays', { n: f.current_streak })} · {f.total_score.toLocaleString()} pts</Text>
                </View>
                <TouchableOpacity style={styles.btnDecline} onPress={() => removeFriend(f.username)}>
                  <Text style={{ color: C.red, fontWeight: '700' }}>✕</Text>
                </TouchableOpacity>
              </View>
            );
          }}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  guestState:     { flex: 1, backgroundColor: C.bg, alignItems: 'center', justifyContent: 'center', padding: 32 },
  guestTitle:     { fontSize: 22, fontWeight: '800', color: C.text, marginBottom: 12 },
  searchRow:      { flexDirection: 'row', alignItems: 'center', marginBottom: 10 },
  friendRow:      { flexDirection: 'row', alignItems: 'center', gap: 12, backgroundColor: C.card, borderWidth: 1, borderColor: C.border, borderRadius: 12, padding: 12, marginBottom: 8 },
  avatar:         { width: 40, height: 40, borderRadius: 20, backgroundColor: C.accent, alignItems: 'center', justifyContent: 'center' },
  avatarText:     { color: '#fff', fontWeight: '800', fontSize: 16 },
  friendName:     { fontWeight: '700', fontSize: 15, color: C.text },
  btnAccept:      { backgroundColor: 'rgba(74,222,128,0.2)', borderRadius: 8, paddingHorizontal: 12, paddingVertical: 7 },
  btnDecline:     { backgroundColor: 'rgba(248,113,113,0.15)', borderRadius: 8, paddingHorizontal: 12, paddingVertical: 7 },
  btnAdd:         { backgroundColor: 'rgba(124,109,255,0.2)', borderRadius: 8, paddingHorizontal: 12, paddingVertical: 7 },
  btnPending:     { backgroundColor: C.surface, borderRadius: 8, paddingHorizontal: 12, paddingVertical: 7 },
  btnPendingText: { color: C.muted, fontWeight: '600' },
});

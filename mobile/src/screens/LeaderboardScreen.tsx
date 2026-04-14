import React, { useState, useCallback } from 'react';
import {
  View, Text, FlatList, StyleSheet, ActivityIndicator, Alert,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { C, S } from '../theme';
import { apiLeaderboard } from '../api';
import { LeaderboardEntry, AuthSession } from '../types';

interface Props { session: AuthSession }

export default function LeaderboardScreen({ session }: Props) {
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useFocusEffect(useCallback(() => { load(); }, []));

  async function load() {
    setLoading(true);
    try {
      const data = await apiLeaderboard(20);
      setEntries(data.entries);
    } catch {
      Alert.alert('Error', 'No se pudo cargar el ranking.');
    } finally {
      setLoading(false);
    }
  }

  const rankEmoji = (r: number) => r === 1 ? '🥇' : r === 2 ? '🥈' : r === 3 ? '🥉' : String(r);
  const rankColor = (r: number) => r === 1 ? '#fbbf24' : r === 2 ? '#94a3b8' : r === 3 ? '#cd7f32' : C.muted;

  return (
    <View style={{ flex: 1, backgroundColor: C.bg }}>
      <Text style={[S.sectionTitle, { padding: 16, paddingBottom: 8 }]}>Ranking global</Text>
      {loading ? (
        <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
          <ActivityIndicator color={C.accent} size="large" />
        </View>
      ) : (
        <FlatList
          data={entries}
          keyExtractor={e => e.username}
          contentContainerStyle={styles.list}
          ListEmptyComponent={<Text style={[S.muted, { textAlign: 'center', marginTop: 40 }]}>Nadie en el ranking todavía</Text>}
          renderItem={({ item: e }) => (
            <View style={[styles.row, e.username === session.username && styles.rowSelf]}>
              <Text style={[styles.rank, { color: rankColor(e.rank) }]}>{rankEmoji(e.rank)}</Text>
              <View style={styles.avatar}>
                <Text style={styles.avatarText}>{e.display_name[0].toUpperCase()}</Text>
              </View>
              <View style={{ flex: 1 }}>
                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                  <Text style={styles.name}>{e.display_name}</Text>
                  {e.username === session.username && (
                    <Text style={{ fontSize: 11, color: C.accent }}>(tú)</Text>
                  )}
                </View>
                <Text style={S.muted}>🔥 {e.current_streak} días de racha</Text>
              </View>
              <Text style={styles.score}>{e.total_score.toLocaleString()}</Text>
            </View>
          )}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  list:       { backgroundColor: C.card, borderWidth: 1, borderColor: C.border, borderRadius: 16, margin: 16, overflow: 'hidden' },
  row:        { flexDirection: 'row', alignItems: 'center', gap: 14, padding: 14, borderBottomWidth: 1, borderColor: C.border },
  rowSelf:    { backgroundColor: 'rgba(124,109,255,0.08)' },
  rank:       { fontSize: 18, fontWeight: '900', width: 28, textAlign: 'center' },
  avatar:     { width: 38, height: 38, borderRadius: 19, backgroundColor: C.accent, alignItems: 'center', justifyContent: 'center' },
  avatarText: { color: '#fff', fontSize: 14, fontWeight: '800' },
  name:       { fontWeight: '700', fontSize: 15, color: C.text },
  score:      { fontSize: 17, fontWeight: '800', color: C.accent },
});

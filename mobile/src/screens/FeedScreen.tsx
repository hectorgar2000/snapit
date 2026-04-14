import React, { useState, useCallback } from 'react';
import {
  View, Text, FlatList, TouchableOpacity, StyleSheet,
  Image, TextInput, Alert, Share, ScrollView,
} from 'react-native';
import { FeedSkeleton } from '../components/Skeleton';
import { useFocusEffect } from '@react-navigation/native';
import { C, S } from '../theme';
import { apiFeed, apiLike, apiUnlike, apiComments, apiPostComment } from '../api';
import { FeedEntry, Comment, AuthSession } from '../types';

interface Props { session: AuthSession }

export default function FeedScreen({ session }: Props) {
  const [entries,      setEntries]      = useState<FeedEntry[]>([]);
  const [loading,      setLoading]      = useState(true);
  const [friendsOnly,  setFriendsOnly]  = useState(false);
  const [openComments, setOpenComments] = useState<number | null>(null);
  const [comments,     setComments]     = useState<Record<number, Comment[]>>({});
  const [commentText,  setCommentText]  = useState('');

  useFocusEffect(useCallback(() => { loadFeed(); }, [friendsOnly]));

  async function loadFeed() {
    setLoading(true);
    try {
      const data = await apiFeed(friendsOnly, session.token);
      setEntries(data.entries);
    } catch {
      Alert.alert('Error', 'No se pudo cargar el feed.');
    } finally {
      setLoading(false);
    }
  }

  async function toggleLike(entry: FeedEntry) {
    if (session.isGuest) { Alert.alert('Regístrate para dar likes'); return; }
    try {
      const fn = entry.user_liked ? apiUnlike : apiLike;
      const res = await fn(entry.submission_id, session.token);
      setEntries(prev => prev.map(e =>
        e.submission_id === entry.submission_id
          ? { ...e, like_count: res.likes, user_liked: !e.user_liked }
          : e
      ));
    } catch {}
  }

  async function loadComments(sid: number) {
    try {
      const data = await apiComments(sid, session.token);
      setComments(prev => ({ ...prev, [sid]: data }));
    } catch {}
  }

  async function postComment(sid: number) {
    if (session.isGuest) { Alert.alert('Regístrate para comentar'); return; }
    if (!commentText.trim()) return;
    try {
      await apiPostComment(sid, commentText.trim(), session.token);
      setCommentText('');
      loadComments(sid);
      setEntries(prev => prev.map(e =>
        e.submission_id === sid ? { ...e, comment_count: e.comment_count + 1 } : e
      ));
    } catch {}
  }

  function toggleComments(sid: number) {
    if (openComments === sid) { setOpenComments(null); return; }
    setOpenComments(sid);
    if (!comments[sid]) loadComments(sid);
  }

  async function shareEntry(entry: FeedEntry) {
    const text = `📸 SnapIT\n${entry.display_name} ${entry.correct ? 'detectó' : 'intentó'} ${entry.object_emoji} ${entry.object_name}\n${entry.correct ? '🎯' : '❌'} ${entry.total_score.toLocaleString()} pts · ${entry.speed_label}\nsnapit.app`;
    await Share.share({ message: text });
  }

  function timeAgo(iso: string) {
    const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
    if (diff < 60) return 'Hace un momento';
    if (diff < 3600) return `Hace ${Math.floor(diff / 60)} min`;
    return `Hace ${Math.floor(diff / 3600)}h`;
  }

  const renderItem = ({ item: e }: { item: FeedEntry }) => (
    <View style={styles.entry}>
      {/* Header */}
      <View style={styles.entryHeader}>
        <View style={styles.avatar}><Text style={styles.avatarText}>{e.display_name[0].toUpperCase()}</Text></View>
        <View style={{ flex: 1 }}>
          <Text style={styles.entryName}>{e.display_name}</Text>
          <Text style={S.muted}>{timeAgo(e.submitted_at)}</Text>
        </View>
        <Text style={[styles.entryScore, { color: e.correct ? C.green : C.red }]}>
          {e.total_score.toLocaleString()} pts
        </Text>
      </View>

      {/* Imagen */}
      {e.annotated_image_b64 ? (
        <Image source={{ uri: `data:image/jpeg;base64,${e.annotated_image_b64}` }}
          style={styles.entryImage} resizeMode="cover" />
      ) : (
        <View style={styles.entryImagePlaceholder}>
          <Text style={{ fontSize: 48 }}>{e.object_emoji}</Text>
        </View>
      )}

      {/* Tags */}
      <View style={styles.tags}>
        <View style={[styles.tag, e.correct ? styles.tagCorrect : styles.tagWrong]}>
          <Text style={[styles.tagText, { color: e.correct ? C.green : C.red }]}>{e.correct ? '✅ Detectado' : '❌ Fallido'}</Text>
        </View>
        <View style={styles.tag}><Text style={styles.tagText}>{e.speed_label}</Text></View>
        <View style={styles.tag}><Text style={styles.tagText}>{e.framing_label}</Text></View>
        {e.correct && <View style={styles.tag}><Text style={styles.tagText}>🎯 {e.confidence_pct}%</Text></View>}
      </View>

      {/* Acciones */}
      <View style={styles.actions}>
        <TouchableOpacity style={[styles.actionBtn, e.user_liked && styles.actionBtnLiked]}
          onPress={() => toggleLike(e)}>
          <Text style={[styles.actionBtnText, e.user_liked && { color: C.accent2 }]}>
            ❤️ {e.like_count}
          </Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.actionBtn} onPress={() => toggleComments(e.submission_id)}>
          <Text style={styles.actionBtnText}>💬 {e.comment_count}</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[styles.actionBtn, { marginLeft: 'auto' }]} onPress={() => shareEntry(e)}>
          <Text style={styles.actionBtnText}>📤</Text>
        </TouchableOpacity>
      </View>

      {/* Comentarios */}
      {openComments === e.submission_id && (
        <View style={styles.commentsSection}>
          {(comments[e.submission_id] || []).map(c => (
            <View key={c.id} style={styles.comment}>
              <View style={styles.commentAvatar}><Text style={styles.commentAvatarText}>{c.display_name[0].toUpperCase()}</Text></View>
              <View style={styles.commentBubble}>
                <Text style={{ color: C.accent, fontSize: 11, fontWeight: '700' }}>{c.display_name}</Text>
                <Text style={{ color: C.text, fontSize: 13, marginTop: 1 }}>{c.text}</Text>
              </View>
            </View>
          ))}
          {!session.isGuest && (
            <View style={styles.commentInput}>
              <TextInput
                style={styles.commentInputField}
                placeholder="Añade un comentario…"
                placeholderTextColor={C.muted}
                value={commentText}
                onChangeText={setCommentText}
                maxLength={280}
                onSubmitEditing={() => postComment(e.submission_id)}
              />
              <TouchableOpacity onPress={() => postComment(e.submission_id)}
                style={{ backgroundColor: C.accent, borderRadius: 16, paddingHorizontal: 14, paddingVertical: 6 }}>
                <Text style={{ color: '#fff', fontWeight: '700' }}>→</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>
      )}
    </View>
  );

  return (
    <View style={{ flex: 1, backgroundColor: C.bg }}>
      {/* Cabecera con toggle amigos */}
      <View style={styles.header}>
        <Text style={S.sectionTitle}>Feed de hoy</Text>
        <TouchableOpacity style={styles.toggleRow} onPress={() => setFriendsOnly(f => !f)}>
          <Text style={S.muted}>Solo amigos</Text>
          <View style={[styles.toggle, friendsOnly && styles.toggleOn]}>
            <View style={[styles.toggleKnob, friendsOnly && styles.toggleKnobOn]} />
          </View>
        </TouchableOpacity>
      </View>

      {loading ? (
        <ScrollView><FeedSkeleton /></ScrollView>
      ) : (
        <FlatList
          data={entries}
          keyExtractor={e => String(e.submission_id)}
          renderItem={renderItem}
          contentContainerStyle={{ padding: 12 }}
          ListEmptyComponent={
            <Text style={[S.muted, { textAlign: 'center', marginTop: 40 }]}>
              {friendsOnly ? '👥 Ningún amigo ha jugado hoy todavía' : '😶 Nadie ha jugado hoy todavía'}
            </Text>
          }
          onRefresh={loadFeed}
          refreshing={loading}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  header:           { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 16, paddingBottom: 0 },
  toggleRow:        { flexDirection: 'row', alignItems: 'center', gap: 8 },
  toggle:           { width: 36, height: 20, backgroundColor: C.border, borderRadius: 10, justifyContent: 'center', paddingHorizontal: 3 },
  toggleOn:         { backgroundColor: C.accent },
  toggleKnob:       { width: 14, height: 14, borderRadius: 7, backgroundColor: '#fff' },
  toggleKnobOn:     { alignSelf: 'flex-end' },
  entry:            { backgroundColor: C.card, borderWidth: 1, borderColor: C.border, borderRadius: 16, marginBottom: 12, overflow: 'hidden' },
  entryHeader:      { flexDirection: 'row', alignItems: 'center', gap: 12, padding: 14 },
  avatar:           { width: 40, height: 40, borderRadius: 20, backgroundColor: C.accent, alignItems: 'center', justifyContent: 'center' },
  avatarText:       { color: '#fff', fontWeight: '800', fontSize: 16 },
  entryName:        { fontWeight: '700', fontSize: 15, color: C.text },
  entryScore:       { fontSize: 18, fontWeight: '800' },
  entryImage:       { width: '100%', height: 220 },
  entryImagePlaceholder: { height: 160, backgroundColor: C.surface, alignItems: 'center', justifyContent: 'center' },
  tags:             { flexDirection: 'row', flexWrap: 'wrap', gap: 6, padding: 10 },
  tag:              { backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, borderRadius: 20, paddingHorizontal: 10, paddingVertical: 3 },
  tagCorrect:       { backgroundColor: 'rgba(74,222,128,0.1)', borderColor: 'rgba(74,222,128,0.3)' },
  tagWrong:         { backgroundColor: 'rgba(248,113,113,0.1)', borderColor: 'rgba(248,113,113,0.3)' },
  tagText:          { fontSize: 11, fontWeight: '600', color: C.muted },
  actions:          { flexDirection: 'row', alignItems: 'center', gap: 8, padding: 8, paddingHorizontal: 16, borderTopWidth: 1, borderColor: C.border },
  actionBtn:        { flexDirection: 'row', alignItems: 'center', backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, borderRadius: 20, paddingHorizontal: 12, paddingVertical: 5 },
  actionBtnLiked:   { backgroundColor: 'rgba(255,109,176,0.12)', borderColor: C.accent2 },
  actionBtnText:    { fontSize: 13, fontWeight: '600', color: C.muted },
  commentsSection:  { padding: 12, paddingTop: 0 },
  comment:          { flexDirection: 'row', gap: 8, marginTop: 8 },
  commentAvatar:    { width: 28, height: 28, borderRadius: 14, backgroundColor: C.accent, alignItems: 'center', justifyContent: 'center' },
  commentAvatarText:{ color: '#fff', fontSize: 11, fontWeight: '800' },
  commentBubble:    { backgroundColor: C.surface, borderRadius: 10, padding: 8, flex: 1 },
  commentInput:     { flexDirection: 'row', gap: 6, marginTop: 10, alignItems: 'center' },
  commentInputField:{ flex: 1, backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, borderRadius: 20, paddingHorizontal: 14, paddingVertical: 6, fontSize: 13, color: C.text },
});

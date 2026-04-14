import React, { useState, useCallback } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  TextInput, Alert,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { C, S } from '../theme';
import { apiMe, apiUpdateProfile, apiChangePassword, apiDeleteAccount, apiHistory } from '../api';
import { clearSession } from '../auth';
import { ProfileSkeleton } from '../components/Skeleton';
import { AuthSession } from '../types';

interface Props {
  session: AuthSession;
  onLogout: () => void;
}

export default function ProfileScreen({ session, onLogout }: Props) {
  const [profile,      setProfile]      = useState<any>(null);
  const [history,      setHistory]      = useState<any[]>([]);
  const [loading,      setLoading]      = useState(true);
  const [editingName,  setEditingName]  = useState(false);
  const [newName,      setNewName]      = useState('');
  const [savingName,   setSavingName]   = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [oldPass,      setOldPass]      = useState('');
  const [newPass,      setNewPass]      = useState('');
  const [savingPass,   setSavingPass]   = useState(false);

  useFocusEffect(useCallback(() => { load(); }, []));

  async function load() {
    setLoading(true);
    try {
      const [me, hist] = await Promise.all([
        apiMe(session.token),
        apiHistory(session.username, session.token),
      ]);
      setProfile(me);
      setHistory(hist.entries?.slice(0, 7) ?? []);
    } catch {
      Alert.alert('Error', 'No se pudo cargar el perfil.');
    } finally {
      setLoading(false);
    }
  }

  async function saveName() {
    if (!newName.trim()) return;
    setSavingName(true);
    try {
      const updated = await apiUpdateProfile(newName.trim(), session.token);
      setProfile(updated);
      setEditingName(false);
      setNewName('');
    } catch (e: any) {
      Alert.alert('Error', e.message);
    } finally {
      setSavingName(false);
    }
  }

  async function savePassword() {
    if (!oldPass || !newPass) return;
    if (newPass.length < 6) {
      Alert.alert('Error', 'La nueva contraseña debe tener al menos 6 caracteres');
      return;
    }
    setSavingPass(true);
    try {
      await apiChangePassword(oldPass, newPass, session.token);
      Alert.alert('✅ Contraseña cambiada', 'Tu contraseña se ha actualizado correctamente.');
      setShowPassword(false);
      setOldPass('');
      setNewPass('');
    } catch (e: any) {
      Alert.alert('Error', e.message);
    } finally {
      setSavingPass(false);
    }
  }

  function confirmLogout() {
    Alert.alert('Cerrar sesión', '¿Seguro que quieres cerrar sesión?', [
      { text: 'Cancelar', style: 'cancel' },
      { text: 'Cerrar sesión', style: 'destructive', onPress: async () => {
        await clearSession();
        onLogout();
      }},
    ]);
  }

  function confirmDelete() {
    Alert.alert(
      '⚠️ Eliminar cuenta',
      'Esta acción es permanente. Se borrarán todos tus datos, puntuaciones e historial.',
      [
        { text: 'Cancelar', style: 'cancel' },
        { text: 'Eliminar', style: 'destructive', onPress: () => {
          if (session.isGuest) {
            deleteAccount('');
          } else {
            Alert.prompt(
              'Confirmar contraseña',
              'Introduce tu contraseña para confirmar la eliminación',
              [
                { text: 'Cancelar', style: 'cancel' },
                { text: 'Eliminar', style: 'destructive', onPress: (pwd?: string) => deleteAccount(pwd ?? '') },
              ],
              'secure-text',
            );
          }
        }},
      ],
    );
  }

  async function deleteAccount(password: string) {
    try {
      await apiDeleteAccount(password, session.token);
      await clearSession();
      onLogout();
    } catch (e: any) {
      Alert.alert('Error', e.message);
    }
  }

  const diffColor = (d: string) =>
    d === 'easy' ? C.green : d === 'medium' ? '#f59e0b' : C.red;

  if (loading) return (
    <ScrollView style={{ flex: 1, backgroundColor: C.bg }}>
      <ProfileSkeleton />
    </ScrollView>
  );

  const displayName = profile?.display_name || session.displayName;

  return (
    <ScrollView style={{ flex: 1, backgroundColor: C.bg }} contentContainerStyle={{ padding: 16 }}>

      {/* ── Avatar + nombre ─────────────────────────────────────────── */}
      <View style={styles.header}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>{displayName[0].toUpperCase()}</Text>
        </View>
        <View style={{ flex: 1 }}>
          {editingName ? (
            <View style={styles.editRow}>
              <TextInput
                style={[S.input, { flex: 1, marginBottom: 0 }]}
                value={newName}
                onChangeText={setNewName}
                placeholder="Nuevo nombre"
                placeholderTextColor={C.muted}
                maxLength={30}
                autoFocus
              />
              <TouchableOpacity style={styles.btnSave} onPress={saveName} disabled={savingName}>
                <Text style={{ color: '#fff', fontWeight: '700' }}>{savingName ? '…' : '✓'}</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.btnCancel} onPress={() => { setEditingName(false); setNewName(''); }}>
                <Text style={{ color: C.muted, fontWeight: '700' }}>✕</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <View style={styles.nameRow}>
              <Text style={styles.displayName}>{displayName}</Text>
              {!session.isGuest && (
                <TouchableOpacity onPress={() => { setNewName(displayName); setEditingName(true); }}>
                  <Text style={{ fontSize: 14 }}>✏️</Text>
                </TouchableOpacity>
              )}
            </View>
          )}
          <Text style={S.muted}>@{session.username}</Text>
          {session.isGuest && (
            <Text style={{ fontSize: 11, color: C.accent, marginTop: 2 }}>👤 Invitado</Text>
          )}
        </View>
      </View>

      {/* ── Stats ───────────────────────────────────────────────────── */}
      <View style={styles.statsRow}>
        <View style={styles.statBox}>
          <Text style={styles.statValue}>{(profile?.total_score ?? 0).toLocaleString()}</Text>
          <Text style={styles.statLabel}>Puntos</Text>
        </View>
        <View style={styles.statBox}>
          <Text style={styles.statValue}>🔥 {profile?.current_streak ?? 0}</Text>
          <Text style={styles.statLabel}>Racha</Text>
        </View>
        <View style={styles.statBox}>
          <Text style={styles.statValue}>⚡ {profile?.max_streak ?? 0}</Text>
          <Text style={styles.statLabel}>Récord</Text>
        </View>
      </View>

      {/* ── Historial reciente ──────────────────────────────────────── */}
      {history.length > 0 && (
        <View style={{ marginBottom: 24 }}>
          <Text style={[S.sectionTitle, { marginBottom: 10 }]}>Historial reciente</Text>
          {history.map((entry: any, i: number) => (
            <View key={i} style={styles.historyRow}>
              <Text style={{ fontSize: 22 }}>{entry.object_emoji}</Text>
              <View style={{ flex: 1 }}>
                <Text style={styles.historyName}>{entry.object_name}</Text>
                <Text style={S.muted}>{entry.date} · {entry.speed_label}</Text>
              </View>
              <View style={{ alignItems: 'flex-end' }}>
                <Text style={[styles.historyScore, { color: entry.correct ? C.green : C.red }]}>
                  {entry.correct ? '✅' : '❌'} {entry.total_score.toLocaleString()}
                </Text>
                <Text style={{ fontSize: 10, color: diffColor(entry.difficulty), fontWeight: '600' }}>
                  {entry.difficulty}
                </Text>
              </View>
            </View>
          ))}
        </View>
      )}

      {history.length === 0 && !loading && (
        <View style={styles.emptyHistory}>
          <Text style={{ fontSize: 32, marginBottom: 8 }}>📷</Text>
          <Text style={S.muted}>Aún no has jugado ningún reto</Text>
        </View>
      )}

      {/* ── Cambiar contraseña ──────────────────────────────────────── */}
      {!session.isGuest && (
        <View style={{ marginBottom: 10 }}>
          <TouchableOpacity style={styles.sectionBtn} onPress={() => setShowPassword(v => !v)}>
            <Text style={styles.sectionBtnText}>🔑 Cambiar contraseña</Text>
            <Text style={S.muted}>{showPassword ? '▲' : '▼'}</Text>
          </TouchableOpacity>
          {showPassword && (
            <View style={styles.expandBox}>
              <TextInput
                style={S.input}
                placeholder="Contraseña actual"
                placeholderTextColor={C.muted}
                secureTextEntry
                value={oldPass}
                onChangeText={setOldPass}
              />
              <TextInput
                style={S.input}
                placeholder="Nueva contraseña (mín. 6 caracteres)"
                placeholderTextColor={C.muted}
                secureTextEntry
                value={newPass}
                onChangeText={setNewPass}
              />
              <TouchableOpacity
                style={[S.btnPrimary, { opacity: savingPass ? 0.6 : 1 }]}
                onPress={savePassword}
                disabled={savingPass}
              >
                <Text style={{ color: '#fff', fontWeight: '800', fontSize: 15 }}>{savingPass ? 'Guardando…' : 'Actualizar contraseña'}</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>
      )}

      {/* ── Cerrar sesión ───────────────────────────────────────────── */}
      <TouchableOpacity style={styles.logoutBtn} onPress={confirmLogout}>
        <Text style={styles.logoutText}>↩ Cerrar sesión</Text>
      </TouchableOpacity>

      {/* ── Eliminar cuenta ─────────────────────────────────────────── */}
      <TouchableOpacity style={styles.deleteBtn} onPress={confirmDelete}>
        <Text style={styles.deleteText}>🗑 Eliminar cuenta</Text>
      </TouchableOpacity>

      <View style={{ height: 32 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  header:         { flexDirection: 'row', alignItems: 'center', gap: 16, marginBottom: 24,
                    backgroundColor: C.card, borderWidth: 1, borderColor: C.border as string,
                    borderRadius: 16, padding: 16 },
  avatar:         { width: 60, height: 60, borderRadius: 30, backgroundColor: C.accent as string,
                    alignItems: 'center', justifyContent: 'center' },
  avatarText:     { color: '#fff', fontSize: 24, fontWeight: '900' },
  nameRow:        { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 2 },
  displayName:    { fontSize: 18, fontWeight: '800', color: C.text },
  editRow:        { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 4 },
  btnSave:        { backgroundColor: C.accent as string, borderRadius: 8, padding: 8 },
  btnCancel:      { backgroundColor: C.surface, borderRadius: 8, padding: 8 },
  statsRow:       { flexDirection: 'row', gap: 10, marginBottom: 24 },
  statBox:        { flex: 1, backgroundColor: C.card, borderWidth: 1, borderColor: C.border as string,
                    borderRadius: 12, padding: 14, alignItems: 'center' },
  statValue:      { fontSize: 18, fontWeight: '900', color: C.text, marginBottom: 2 },
  statLabel:      { fontSize: 11, color: C.muted, fontWeight: '600' },
  historyRow:     { flexDirection: 'row', alignItems: 'center', gap: 12,
                    backgroundColor: C.card, borderWidth: 1, borderColor: C.border as string,
                    borderRadius: 12, padding: 12, marginBottom: 8 },
  historyName:    { fontWeight: '700', fontSize: 14, color: C.text },
  historyScore:   { fontWeight: '800', fontSize: 14 },
  emptyHistory:   { alignItems: 'center', paddingVertical: 32, marginBottom: 24 },
  sectionBtn:     { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
                    backgroundColor: C.card, borderWidth: 1, borderColor: C.border as string,
                    borderRadius: 12, padding: 16, marginBottom: 4 },
  sectionBtnText: { fontWeight: '700', color: C.text, fontSize: 15 },
  expandBox:      { backgroundColor: C.card, borderWidth: 1, borderColor: C.border as string,
                    borderRadius: 12, padding: 16, marginBottom: 8 },
  logoutBtn:      { backgroundColor: C.surface, borderWidth: 1, borderColor: C.border as string,
                    borderRadius: 12, padding: 16, alignItems: 'center', marginBottom: 10 },
  logoutText:     { fontWeight: '700', color: C.text, fontSize: 15 },
  deleteBtn:      { backgroundColor: 'rgba(248,113,113,0.08)', borderWidth: 1,
                    borderColor: 'rgba(248,113,113,0.3)', borderRadius: 12,
                    padding: 16, alignItems: 'center' },
  deleteText:     { fontWeight: '700', color: C.red, fontSize: 15 },
});

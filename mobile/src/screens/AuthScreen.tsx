import React, { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  ScrollView, ActivityIndicator, KeyboardAvoidingView, Platform, Alert,
} from 'react-native';
import { C, S } from '../theme';
import { apiLogin, apiRegister, apiGuest } from '../api';
import { saveSession } from '../auth';
import { AuthSession } from '../types';

type Tab = 'login' | 'register' | 'guest';

interface Props {
  onAuth: (session: AuthSession) => void;
}

export default function AuthScreen({ onAuth }: Props) {
  const [tab, setTab] = useState<Tab>('login');
  const [loading, setLoading] = useState(false);

  // Login
  const [loginEmail,    setLoginEmail]    = useState('');
  const [loginPassword, setLoginPassword] = useState('');

  // Register
  const [regUsername,    setRegUsername]    = useState('');
  const [regDisplayName, setRegDisplayName] = useState('');
  const [regEmail,       setRegEmail]       = useState('');
  const [regPassword,    setRegPassword]    = useState('');

  // Guest
  const [guestUsername,    setGuestUsername]    = useState('');
  const [guestDisplayName, setGuestDisplayName] = useState('');

  async function doLogin() {
    if (!loginEmail || !loginPassword) { Alert.alert('Rellena todos los campos'); return; }
    setLoading(true);
    try {
      const data = await apiLogin(loginEmail.trim(), loginPassword);
      onAuth(await saveSession(data));
    } catch (e: any) {
      Alert.alert('Error', e.message);
    } finally {
      setLoading(false);
    }
  }

  async function doRegister() {
    if (!regUsername || !regEmail || !regPassword) { Alert.alert('Rellena todos los campos obligatorios'); return; }
    if (regPassword.length < 6) { Alert.alert('La contraseña debe tener al menos 6 caracteres'); return; }
    setLoading(true);
    try {
      const data = await apiRegister({
        username:     regUsername.trim().toLowerCase().replace(/\s+/g, '_'),
        display_name: regDisplayName.trim() || regUsername.trim(),
        email:        regEmail.trim(),
        password:     regPassword,
      });
      onAuth(await saveSession(data));
    } catch (e: any) {
      Alert.alert('Error', e.message);
    } finally {
      setLoading(false);
    }
  }

  async function doGuest() {
    if (!guestUsername.trim()) { Alert.alert('Elige un nombre de usuario'); return; }
    setLoading(true);
    try {
      const u = guestUsername.trim().toLowerCase().replace(/\s+/g, '_');
      const d = guestDisplayName.trim() || u;
      const data = await apiGuest(u, d);
      onAuth(await saveSession({ ...data, is_guest: true }));
    } catch (e: any) {
      Alert.alert('Error', e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <KeyboardAvoidingView
      style={{ flex: 1, backgroundColor: C.bg }}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
        {/* Logo */}
        <View style={styles.logoRow}>
          <Text style={styles.logo}>Snap<Text style={{ color: C.accent }}>IT</Text></Text>
          <Text style={styles.tagline}>El juego diario de detección de objetos</Text>
        </View>

        {/* Tab switcher */}
        <View style={styles.tabRow}>
          {(['login', 'register', 'guest'] as Tab[]).map(t => (
            <TouchableOpacity
              key={t}
              style={[styles.tab, tab === t && styles.tabActive]}
              onPress={() => setTab(t)}
            >
              <Text style={[styles.tabText, tab === t && { color: '#fff' }]}>
                {t === 'login' ? 'Entrar' : t === 'register' ? 'Registro' : 'Invitado'}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* LOGIN */}
        {tab === 'login' && (
          <View>
            <TextInput style={S.input} placeholder="Email" placeholderTextColor={C.muted}
              value={loginEmail} onChangeText={setLoginEmail}
              keyboardType="email-address" autoCapitalize="none" />
            <TextInput style={S.input} placeholder="Contraseña" placeholderTextColor={C.muted}
              value={loginPassword} onChangeText={setLoginPassword}
              secureTextEntry onSubmitEditing={doLogin} />
            <TouchableOpacity style={S.btnPrimary} onPress={doLogin} disabled={loading}>
              {loading ? <ActivityIndicator color="#fff" /> : <Text style={S.btnText}>Iniciar sesión →</Text>}
            </TouchableOpacity>
          </View>
        )}

        {/* REGISTER */}
        {tab === 'register' && (
          <View>
            <TextInput style={S.input} placeholder="Nombre de usuario" placeholderTextColor={C.muted}
              value={regUsername} onChangeText={setRegUsername}
              autoCapitalize="none" maxLength={20} />
            <TextInput style={S.input} placeholder="Nombre visible (opcional)" placeholderTextColor={C.muted}
              value={regDisplayName} onChangeText={setRegDisplayName} maxLength={30} />
            <TextInput style={S.input} placeholder="Email" placeholderTextColor={C.muted}
              value={regEmail} onChangeText={setRegEmail}
              keyboardType="email-address" autoCapitalize="none" />
            <TextInput style={S.input} placeholder="Contraseña (mín. 6 caracteres)" placeholderTextColor={C.muted}
              value={regPassword} onChangeText={setRegPassword}
              secureTextEntry onSubmitEditing={doRegister} />
            <TouchableOpacity style={S.btnPrimary} onPress={doRegister} disabled={loading}>
              {loading ? <ActivityIndicator color="#fff" /> : <Text style={S.btnText}>Crear cuenta →</Text>}
            </TouchableOpacity>
          </View>
        )}

        {/* GUEST */}
        {tab === 'guest' && (
          <View>
            <Text style={[S.muted, { marginBottom: 12 }]}>
              ⚠️ Sin cuenta tu racha no persiste entre dispositivos
            </Text>
            <TextInput style={S.input} placeholder="Nombre de usuario" placeholderTextColor={C.muted}
              value={guestUsername} onChangeText={setGuestUsername}
              autoCapitalize="none" maxLength={20} />
            <TextInput style={S.input} placeholder="Nombre visible (opcional)" placeholderTextColor={C.muted}
              value={guestDisplayName} onChangeText={setGuestDisplayName} maxLength={30} />
            <TouchableOpacity style={S.btnSecondary} onPress={doGuest} disabled={loading}>
              {loading ? <ActivityIndicator color={C.text} /> : <Text style={S.btnText}>Jugar como invitado →</Text>}
            </TouchableOpacity>
          </View>
        )}
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container:  { flexGrow: 1, padding: 24, justifyContent: 'center' },
  logoRow:    { alignItems: 'center', marginBottom: 32 },
  logo:       { fontSize: 40, fontWeight: '900', color: C.text, letterSpacing: -1 },
  tagline:    { fontSize: 13, color: C.muted, marginTop: 6 },
  tabRow:     { flexDirection: 'row', backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, borderRadius: 10, padding: 4, marginBottom: 20, gap: 4 },
  tab:        { flex: 1, paddingVertical: 9, borderRadius: 7, alignItems: 'center' },
  tabActive:  { backgroundColor: C.accent },
  tabText:    { fontSize: 13, fontWeight: '700', color: C.muted },
});

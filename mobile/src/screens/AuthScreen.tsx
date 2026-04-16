import React, { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  ScrollView, ActivityIndicator, KeyboardAvoidingView, Platform, Alert,
} from 'react-native';
import { useTranslation } from 'react-i18next';
import { C, S } from '../theme';
import { apiLogin, apiRegister, apiGuest } from '../api';
import { saveSession } from '../auth';
import { AuthSession } from '../types';

type Tab = 'login' | 'register' | 'guest';
interface Props { onAuth: (session: AuthSession) => void }

export default function AuthScreen({ onAuth }: Props) {
  const { t } = useTranslation();

  const [tab,     setTab]     = useState<Tab>('login');
  const [loading, setLoading] = useState(false);

  const [loginEmail,    setLoginEmail]    = useState('');
  const [loginPassword, setLoginPassword] = useState('');

  const [regUsername,    setRegUsername]    = useState('');
  const [regDisplayName, setRegDisplayName] = useState('');
  const [regEmail,       setRegEmail]       = useState('');
  const [regPassword,    setRegPassword]    = useState('');

  const [guestUsername,    setGuestUsername]    = useState('');
  const [guestDisplayName, setGuestDisplayName] = useState('');

  async function doLogin() {
    if (!loginEmail || !loginPassword) { Alert.alert(t('auth.fillAll')); return; }
    setLoading(true);
    try {
      onAuth(await saveSession(await apiLogin(loginEmail.trim(), loginPassword)));
    } catch (e: any) {
      Alert.alert(t('common.error'), e.message);
    } finally { setLoading(false); }
  }

  async function doRegister() {
    if (!regUsername || !regEmail || !regPassword) { Alert.alert(t('auth.fillRequired')); return; }
    if (regPassword.length < 6) { Alert.alert(t('auth.passwordTooShort')); return; }
    setLoading(true);
    try {
      onAuth(await saveSession(await apiRegister({
        username:     regUsername.trim().toLowerCase().replace(/\s+/g, '_'),
        display_name: regDisplayName.trim() || regUsername.trim(),
        email:        regEmail.trim(),
        password:     regPassword,
      })));
    } catch (e: any) {
      Alert.alert(t('common.error'), e.message);
    } finally { setLoading(false); }
  }

  async function doGuest() {
    if (!guestUsername.trim()) { Alert.alert(t('auth.chooseUsername')); return; }
    setLoading(true);
    try {
      const u = guestUsername.trim().toLowerCase().replace(/\s+/g, '_');
      const d = guestDisplayName.trim() || u;
      onAuth(await saveSession({ ...await apiGuest(u, d), is_guest: true }));
    } catch (e: any) {
      Alert.alert(t('common.error'), e.message);
    } finally { setLoading(false); }
  }

  const TABS: { key: Tab; label: string }[] = [
    { key: 'login',    label: t('auth.tabLogin') },
    { key: 'register', label: t('auth.tabRegister') },
    { key: 'guest',    label: t('auth.tabGuest') },
  ];

  return (
    <KeyboardAvoidingView
      style={{ flex: 1, backgroundColor: C.bg }}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
        <View style={styles.logoRow}>
          <Text style={styles.logo}>Snap<Text style={{ color: C.accent }}>IT</Text></Text>
          <Text style={styles.tagline}>{t('auth.tagline')}</Text>
        </View>

        <View style={styles.tabRow}>
          {TABS.map(({ key, label }) => (
            <TouchableOpacity
              key={key}
              style={[styles.tab, tab === key && styles.tabActive]}
              onPress={() => setTab(key)}
            >
              <Text style={[styles.tabText, tab === key && { color: '#fff' }]}>{label}</Text>
            </TouchableOpacity>
          ))}
        </View>

        {tab === 'login' && (
          <View>
            <TextInput style={S.input} placeholder={t('auth.email')} placeholderTextColor={C.muted}
              value={loginEmail} onChangeText={setLoginEmail}
              keyboardType="email-address" autoCapitalize="none" />
            <TextInput style={S.input} placeholder={t('auth.password')} placeholderTextColor={C.muted}
              value={loginPassword} onChangeText={setLoginPassword}
              secureTextEntry onSubmitEditing={doLogin} />
            <TouchableOpacity style={S.btnPrimary} onPress={doLogin} disabled={loading}>
              {loading ? <ActivityIndicator color="#fff" /> : <Text style={S.btnText}>{t('auth.loginBtn')}</Text>}
            </TouchableOpacity>
          </View>
        )}

        {tab === 'register' && (
          <View>
            <TextInput style={S.input} placeholder={t('auth.username')} placeholderTextColor={C.muted}
              value={regUsername} onChangeText={setRegUsername} autoCapitalize="none" maxLength={20} />
            <TextInput style={S.input} placeholder={t('auth.displayName')} placeholderTextColor={C.muted}
              value={regDisplayName} onChangeText={setRegDisplayName} maxLength={30} />
            <TextInput style={S.input} placeholder={t('auth.email')} placeholderTextColor={C.muted}
              value={regEmail} onChangeText={setRegEmail} keyboardType="email-address" autoCapitalize="none" />
            <TextInput style={S.input} placeholder={t('auth.passwordMin')} placeholderTextColor={C.muted}
              value={regPassword} onChangeText={setRegPassword}
              secureTextEntry onSubmitEditing={doRegister} />
            <TouchableOpacity style={S.btnPrimary} onPress={doRegister} disabled={loading}>
              {loading ? <ActivityIndicator color="#fff" /> : <Text style={S.btnText}>{t('auth.registerBtn')}</Text>}
            </TouchableOpacity>
          </View>
        )}

        {tab === 'guest' && (
          <View>
            <Text style={[S.muted, { marginBottom: 12 }]}>{t('auth.guestWarning')}</Text>
            <TextInput style={S.input} placeholder={t('auth.username')} placeholderTextColor={C.muted}
              value={guestUsername} onChangeText={setGuestUsername} autoCapitalize="none" maxLength={20} />
            <TextInput style={S.input} placeholder={t('auth.displayName')} placeholderTextColor={C.muted}
              value={guestDisplayName} onChangeText={setGuestDisplayName} maxLength={30} />
            <TouchableOpacity style={S.btnSecondary} onPress={doGuest} disabled={loading}>
              {loading ? <ActivityIndicator color={C.text} /> : <Text style={S.btnText}>{t('auth.guestBtn')}</Text>}
            </TouchableOpacity>
          </View>
        )}
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flexGrow: 1, padding: 24, justifyContent: 'center' },
  logoRow:   { alignItems: 'center', marginBottom: 32 },
  logo:      { fontSize: 40, fontWeight: '900', color: C.text, letterSpacing: -1 },
  tagline:   { fontSize: 13, color: C.muted, marginTop: 6 },
  tabRow:    { flexDirection: 'row', backgroundColor: C.surface, borderWidth: 1, borderColor: C.border,
               borderRadius: 10, padding: 4, marginBottom: 20, gap: 4 },
  tab:       { flex: 1, paddingVertical: 9, borderRadius: 7, alignItems: 'center' },
  tabActive: { backgroundColor: C.accent },
  tabText:   { fontSize: 13, fontWeight: '700', color: C.muted },
});

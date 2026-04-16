import React, { useState, useEffect } from 'react';
import { View, Text, ActivityIndicator, Platform } from 'react-native';
import { NavigationContainer, DefaultTheme } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import * as Notifications from 'expo-notifications';
import AsyncStorage from '@react-native-async-storage/async-storage';
import './src/i18n'; // Inicializar i18n antes que cualquier pantalla

import { AuthSession } from './src/types';
import { loadSession } from './src/auth';
import { apiSavePushToken } from './src/api';
import { C } from './src/theme';

import AuthScreen        from './src/screens/AuthScreen';
import OnboardingScreen  from './src/screens/OnboardingScreen';
import PlayScreen        from './src/screens/PlayScreen';
import FeedScreen        from './src/screens/FeedScreen';
import FriendsScreen     from './src/screens/FriendsScreen';
import LeaderboardScreen from './src/screens/LeaderboardScreen';
import ProfileScreen     from './src/screens/ProfileScreen';

const Tab = createBottomTabNavigator();
const ONBOARDING_KEY = 'snapit_onboarding_done';

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert:  true,
    shouldShowBanner: true,
    shouldShowList:   true,
    shouldPlaySound:  true,
    shouldSetBadge:   false,
  }),
});

const NavTheme = {
  ...DefaultTheme,
  colors: {
    ...DefaultTheme.colors,
    background:   C.bg,
    card:         C.surface,
    border:       C.border,
    text:         C.text,
    primary:      C.accent,
    notification: C.accent2,
  },
};

const TAB_ICONS: Record<string, string> = {
  Jugar: '📷', Feed: '🌐', Amigos: '👥', Ranking: '🏆', Perfil: '👤',
};

function getDailyNotifTime(d: Date): Date {
  const dateStr = `snapit_v1:${d.toISOString().split('T')[0]}`;
  let hash = 0;
  for (let i = 0; i < dateStr.length; i++) {
    hash = Math.imul(31, hash) + dateStr.charCodeAt(i) | 0;
  }
  const minutesOffset = Math.abs(hash) % 720;
  const trigger = new Date(d);
  trigger.setHours(8 + Math.floor(minutesOffset / 60), minutesOffset % 60, 0, 0);
  return trigger;
}

async function setupNotifications(authToken: string) {
  const { status } = await Notifications.requestPermissionsAsync();
  if (status !== 'granted') return;

  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('daily', {
      name: 'Reto diario',
      importance: Notifications.AndroidImportance.HIGH,
    });
  }

  await Notifications.cancelAllScheduledNotificationsAsync();
  const now = new Date();
  for (let offset = 0; offset <= 1; offset++) {
    const day = new Date(now);
    day.setDate(day.getDate() + offset);
    const trigger = getDailyNotifTime(day);
    if (trigger > now) {
      await Notifications.scheduleNotificationAsync({
        content: {
          title: '📷 SnapIT — ¡Ya puedes jugar!',
          body:  'El reto de hoy ya está disponible. ¿Lo detectas?',
          sound: true,
        },
        trigger: { type: Notifications.SchedulableTriggerInputTypes.DATE, date: trigger },
      });
    }
  }

  try {
    const { data } = await Notifications.getExpoPushTokenAsync();
    await apiSavePushToken(data, authToken);
  } catch { /* simulador o sin conexión */ }
}

export default function App() {
  const [session,     setSession]     = useState<AuthSession | null>(null);
  const [checking,    setChecking]    = useState(true);
  const [onboarding,  setOnboarding]  = useState(false);

  useEffect(() => {
    Promise.all([
      loadSession(),
      AsyncStorage.getItem(ONBOARDING_KEY),
    ]).then(([s, done]) => {
      setSession(s);
      setOnboarding(!done);
      setChecking(false);
    });
  }, []);

  useEffect(() => {
    if (session && !session.isGuest) {
      setupNotifications(session.token);
    }
  }, [session]);

  async function handleOnboardingDone() {
    await AsyncStorage.setItem(ONBOARDING_KEY, 'true');
    setOnboarding(false);
  }

  function handleLogout() {
    setSession(null);
  }

  if (checking) return (
    <View style={{ flex: 1, backgroundColor: C.bg, alignItems: 'center', justifyContent: 'center' }}>
      <ActivityIndicator color={C.accent} size="large" />
    </View>
  );

  if (onboarding) return (
    <SafeAreaProvider style={{ backgroundColor: C.bg }}>
      <StatusBar style="light" />
      <OnboardingScreen onDone={handleOnboardingDone} />
    </SafeAreaProvider>
  );

  if (!session) return (
    <SafeAreaProvider style={{ backgroundColor: C.bg }}>
      <StatusBar style="light" />
      <AuthScreen onAuth={setSession} />
    </SafeAreaProvider>
  );

  return (
    <SafeAreaProvider style={{ backgroundColor: C.bg }}>
      <StatusBar style="light" />
      <NavigationContainer theme={NavTheme}>
        <Tab.Navigator
          screenOptions={({ route }) => ({
            headerStyle:             { backgroundColor: C.surface, borderBottomColor: C.border, borderBottomWidth: 1 },
            headerTitleStyle:        { color: C.text, fontWeight: '800', fontSize: 18 },
            tabBarStyle:             { backgroundColor: C.surface, borderTopColor: C.border, borderTopWidth: 1 },
            tabBarActiveTintColor:   C.accent,
            tabBarInactiveTintColor: C.muted,
            tabBarLabelStyle:        { fontSize: 11, fontWeight: '700' },
            tabBarIcon: ({ color, size }) => (
              <Text style={{ fontSize: size - 2, color }}>{TAB_ICONS[route.name] ?? '●'}</Text>
            ),
          })}
        >
          <Tab.Screen
            name="Jugar"
            options={{ title: 'SnapIT', headerRight: () => (
              <Text style={{ color: C.muted, marginRight: 16, fontSize: 13 }}>
                {session.isGuest ? '👤 Invitado' : `@${session.username}`}
              </Text>
            )}}
          >
            {() => <PlayScreen session={session} />}
          </Tab.Screen>

          <Tab.Screen name="Feed">
            {() => <FeedScreen session={session} />}
          </Tab.Screen>

          <Tab.Screen name="Amigos">
            {() => <FriendsScreen session={session} />}
          </Tab.Screen>

          <Tab.Screen name="Ranking">
            {() => <LeaderboardScreen session={session} />}
          </Tab.Screen>

          <Tab.Screen name="Perfil" options={{ title: 'Mi perfil' }}>
            {() => <ProfileScreen session={session} onLogout={handleLogout} />}
          </Tab.Screen>
        </Tab.Navigator>
      </NavigationContainer>
    </SafeAreaProvider>
  );
}

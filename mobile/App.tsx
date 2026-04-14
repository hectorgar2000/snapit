import React, { useState, useEffect } from 'react';
import { View, Text, ActivityIndicator } from 'react-native';
import { NavigationContainer, DefaultTheme } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';

import { AuthSession } from './src/types';
import { loadSession } from './src/auth';
import { C } from './src/theme';

import AuthScreen        from './src/screens/AuthScreen';
import PlayScreen        from './src/screens/PlayScreen';
import FeedScreen        from './src/screens/FeedScreen';
import FriendsScreen     from './src/screens/FriendsScreen';
import LeaderboardScreen from './src/screens/LeaderboardScreen';

const Tab = createBottomTabNavigator();

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
  Jugar: '📷', Feed: '🌐', Amigos: '👥', Ranking: '🏆',
};

export default function App() {
  const [session,  setSession]  = useState<AuthSession | null>(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    loadSession().then(s => { setSession(s); setChecking(false); });
  }, []);

  if (checking) return (
    <View style={{ flex: 1, backgroundColor: C.bg, alignItems: 'center', justifyContent: 'center' }}>
      <ActivityIndicator color={C.accent} size="large" />
    </View>
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
        </Tab.Navigator>
      </NavigationContainer>
    </SafeAreaProvider>
  );
}

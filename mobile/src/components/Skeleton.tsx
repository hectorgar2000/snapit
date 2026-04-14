import React, { useEffect, useRef } from 'react';
import { Animated, View, ViewStyle } from 'react-native';
import { C } from '../theme';

interface SkeletonProps {
  width?: number | string;
  height: number;
  borderRadius?: number;
  style?: ViewStyle;
}

export function Skeleton({ width = '100%', height, borderRadius = 8, style }: SkeletonProps) {
  const opacity = useRef(new Animated.Value(0.4)).current;

  useEffect(() => {
    const anim = Animated.loop(
      Animated.sequence([
        Animated.timing(opacity, { toValue: 0.85, duration: 700, useNativeDriver: true }),
        Animated.timing(opacity, { toValue: 0.4,  duration: 700, useNativeDriver: true }),
      ])
    );
    anim.start();
    return () => anim.stop();
  }, []);

  return (
    <Animated.View
      style={[{ width: width as any, height, borderRadius, backgroundColor: C.surface }, style, { opacity }]}
    />
  );
}

// ── Skeleton layouts por pantalla ─────────────────────────────────────────────

export function FeedSkeleton() {
  return (
    <View style={{ padding: 12 }}>
      {[1, 2, 3].map(i => (
        <View key={i} style={{ backgroundColor: C.card, borderWidth: 1, borderColor: C.border as string,
          borderRadius: 16, marginBottom: 12, overflow: 'hidden' }}>
          {/* Header */}
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12, padding: 14 }}>
            <Skeleton width={40} height={40} borderRadius={20} />
            <View style={{ gap: 6 }}>
              <Skeleton width={120} height={14} />
              <Skeleton width={80}  height={11} />
            </View>
          </View>
          {/* Image area */}
          <Skeleton width="100%" height={200} borderRadius={0} />
          {/* Tags */}
          <View style={{ flexDirection: 'row', gap: 6, padding: 10 }}>
            <Skeleton width={80}  height={24} borderRadius={20} />
            <Skeleton width={60}  height={24} borderRadius={20} />
            <Skeleton width={70}  height={24} borderRadius={20} />
          </View>
        </View>
      ))}
    </View>
  );
}

export function LeaderboardSkeleton() {
  return (
    <View style={{ backgroundColor: C.card, borderWidth: 1, borderColor: C.border as string,
      borderRadius: 16, margin: 16, overflow: 'hidden' }}>
      {[1, 2, 3, 4, 5, 6, 7, 8].map(i => (
        <View key={i} style={{ flexDirection: 'row', alignItems: 'center',
          gap: 14, padding: 14, borderBottomWidth: i < 8 ? 1 : 0, borderColor: C.border as string }}>
          <Skeleton width={28} height={22} borderRadius={6} />
          <Skeleton width={38} height={38} borderRadius={19} />
          <View style={{ flex: 1, gap: 6 }}>
            <Skeleton width={100} height={14} />
            <Skeleton width={70}  height={11} />
          </View>
          <Skeleton width={55} height={20} borderRadius={6} />
        </View>
      ))}
    </View>
  );
}

export function ProfileSkeleton() {
  return (
    <View style={{ padding: 16 }}>
      {/* Header */}
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 16, marginBottom: 24,
        backgroundColor: C.card, borderWidth: 1, borderColor: C.border as string,
        borderRadius: 16, padding: 16 }}>
        <Skeleton width={60} height={60} borderRadius={30} />
        <View style={{ gap: 8 }}>
          <Skeleton width={140} height={18} />
          <Skeleton width={90}  height={13} />
        </View>
      </View>
      {/* Stats */}
      <View style={{ flexDirection: 'row', gap: 10, marginBottom: 24 }}>
        {[1, 2, 3].map(i => (
          <View key={i} style={{ flex: 1, backgroundColor: C.card, borderWidth: 1,
            borderColor: C.border as string, borderRadius: 12, padding: 14, alignItems: 'center', gap: 8 }}>
            <Skeleton width={60} height={20} />
            <Skeleton width={50} height={11} />
          </View>
        ))}
      </View>
      {/* History rows */}
      {[1, 2, 3, 4, 5].map(i => (
        <View key={i} style={{ flexDirection: 'row', alignItems: 'center', gap: 12,
          backgroundColor: C.card, borderWidth: 1, borderColor: C.border as string,
          borderRadius: 12, padding: 12, marginBottom: 8 }}>
          <Skeleton width={36} height={36} borderRadius={8} />
          <View style={{ flex: 1, gap: 6 }}>
            <Skeleton width={110} height={14} />
            <Skeleton width={80}  height={11} />
          </View>
          <Skeleton width={60} height={16} />
        </View>
      ))}
    </View>
  );
}

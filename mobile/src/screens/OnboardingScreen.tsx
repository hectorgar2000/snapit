import React, { useRef, useState } from 'react';
import {
  View, Text, FlatList, TouchableOpacity, StyleSheet,
  Dimensions, Animated,
} from 'react-native';
import { C } from '../theme';

const { width: SCREEN_W } = Dimensions.get('window');

const SLIDES = [
  {
    emoji: '📷',
    title: 'Bienvenido a SnapIT',
    body:  'El juego diario donde la IA te pide un objeto y tú lo tienes que fotografiar. Como Wordle, pero con tu cámara.',
  },
  {
    emoji: '🎯',
    title: 'Detecta y puntúa',
    body:  'Cuanto más preciso, rápido y bien encuadrado, más puntos. Tienes 3 intentos para conseguir la mejor puntuación.',
  },
  {
    emoji: '🏆',
    title: 'Compite cada día',
    body:  'Compara tus resultados con amigos en el feed, sube en el ranking global y mantén tu racha diaria.',
  },
];

interface Props { onDone: () => void }

export default function OnboardingScreen({ onDone }: Props) {
  const [index, setIndex]   = useState(0);
  const flatRef             = useRef<FlatList>(null);
  const scrollX             = useRef(new Animated.Value(0)).current;

  function next() {
    if (index < SLIDES.length - 1) {
      flatRef.current?.scrollToIndex({ index: index + 1, animated: true });
      setIndex(i => i + 1);
    } else {
      onDone();
    }
  }

  function onScroll(e: any) {
    const newIndex = Math.round(e.nativeEvent.contentOffset.x / SCREEN_W);
    setIndex(newIndex);
  }

  return (
    <View style={styles.container}>
      <Animated.FlatList
        ref={flatRef}
        data={SLIDES}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        keyExtractor={(_, i) => String(i)}
        onScroll={Animated.event([{ nativeEvent: { contentOffset: { x: scrollX } } }], { useNativeDriver: false })}
        onMomentumScrollEnd={onScroll}
        renderItem={({ item }) => (
          <View style={styles.slide}>
            <Text style={styles.emoji}>{item.emoji}</Text>
            <Text style={styles.title}>{item.title}</Text>
            <Text style={styles.body}>{item.body}</Text>
          </View>
        )}
      />

      {/* Dots */}
      <View style={styles.dots}>
        {SLIDES.map((_, i) => (
          <View key={i} style={[styles.dot, i === index && styles.dotActive]} />
        ))}
      </View>

      {/* Button */}
      <View style={styles.btnContainer}>
        <TouchableOpacity style={styles.btn} onPress={next}>
          <Text style={styles.btnText}>
            {index === SLIDES.length - 1 ? '¡Empezar a jugar!' : 'Siguiente →'}
          </Text>
        </TouchableOpacity>
        {index < SLIDES.length - 1 && (
          <TouchableOpacity onPress={onDone} style={{ marginTop: 14 }}>
            <Text style={{ color: C.muted, fontSize: 14 }}>Saltar</Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container:    { flex: 1, backgroundColor: C.bg },
  slide:        { width: SCREEN_W, flex: 1, alignItems: 'center', justifyContent: 'center',
                  paddingHorizontal: 40 },
  emoji:        { fontSize: 80, marginBottom: 24 },
  title:        { fontSize: 26, fontWeight: '900', color: C.text, textAlign: 'center', marginBottom: 16 },
  body:         { fontSize: 16, color: C.muted, textAlign: 'center', lineHeight: 24 },
  dots:         { flexDirection: 'row', justifyContent: 'center', gap: 8, paddingBottom: 20 },
  dot:          { width: 8, height: 8, borderRadius: 4, backgroundColor: C.border },
  dotActive:    { width: 24, backgroundColor: C.accent },
  btnContainer: { paddingHorizontal: 32, paddingBottom: 48, alignItems: 'center' },
  btn:          { backgroundColor: C.accent, borderRadius: 14, paddingVertical: 16,
                  alignItems: 'center', width: '100%' },
  btnText:      { color: '#fff', fontSize: 17, fontWeight: '800' },
});

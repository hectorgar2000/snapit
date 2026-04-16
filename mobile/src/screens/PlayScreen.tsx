import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, ScrollView,
  Image, ActivityIndicator, Alert, Share, Platform,
} from 'react-native';
import { CameraView, CameraType, useCameraPermissions } from 'expo-camera';
import { useTranslation } from 'react-i18next';
import { C, S } from '../theme';
import { apiToday, apiWeek, apiSubmit } from '../api';
import { saveScoreToday, getNotifEpoch } from '../auth';
import { AuthSession, Challenge, ScoreResult, WeekDay } from '../types';

interface Props { session: AuthSession }

type Screen = 'challenge' | 'camera' | 'preview' | 'score' | 'done';

export default function PlayScreen({ session }: Props) {
  const { t, i18n: i18nInstance } = useTranslation();

  const [permission, requestPermission] = useCameraPermissions();
  const [screen,       setScreen]       = useState<Screen>('challenge');
  const [challenge,    setChallenge]    = useState<Challenge | null>(null);
  const [week,         setWeek]         = useState<WeekDay[]>([]);
  const [photoUri,     setPhotoUri]     = useState<string | null>(null);
  const [score,        setScore]        = useState<ScoreResult | null>(null);
  const [loading,      setLoading]      = useState(false);
  const [attempt,      setAttempt]      = useState(1);
  const [elapsed,      setElapsed]      = useState(0);
  const [notifTime,    setNotifTime]    = useState<number | null>(null);

  const cameraRef  = useRef<CameraView>(null);
  const timerRef   = useRef<ReturnType<typeof setInterval> | null>(null);

  const startTimer = useCallback((startEpoch: number) => {
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startEpoch) / 1000));
    }, 1000);
  }, []);

  useEffect(() => {
    loadData();
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, []);

  async function loadData() {
    try {
      const [ch, wk, epoch] = await Promise.all([
        apiToday(session.token),
        apiWeek(),
        getNotifEpoch(),
      ]);
      setChallenge(ch);
      setWeek(wk.week);
      if (ch.already_done) {
        setScreen('done');
      } else {
        const ts = epoch || Date.now();
        setNotifTime(ts);
        startTimer(ts);
      }
    } catch (e) {
      Alert.alert(t('play.noConnectionTitle'), t('play.noConnectionBody'));
    }
  }

  async function openCamera() {
    if (!permission?.granted) {
      const { granted } = await requestPermission();
      if (!granted) { Alert.alert(t('play.permissionDenied'), t('play.cameraPermission')); return; }
    }
    setScreen('camera');
  }

  async function takePhoto() {
    if (!cameraRef.current) return;
    try {
      const photo = await cameraRef.current.takePictureAsync({ quality: 0.85 });
      if (photo) { setPhotoUri(photo.uri); setScreen('preview'); }
    } catch {
      Alert.alert(t('common.error'), t('play.photoError'));
    }
  }

  async function submitPhoto() {
    if (!photoUri || !challenge) return;
    setLoading(true);
    try {
      const secs = notifTime ? Math.floor((Date.now() - notifTime) / 1000) : 0;
      const result = await apiSubmit({
        username: session.username,
        displayName: session.displayName,
        secondsSinceNotif: secs,
        attemptNumber: attempt,
        photoUri,
        token: session.token,
      });
      if (timerRef.current) clearInterval(timerRef.current);
      await saveScoreToday(result.total_score);
      setScore(result);
      setScreen('score');
    } catch (e: any) {
      Alert.alert(t('common.error'), e.message || t('play.submitError'));
    } finally {
      setLoading(false);
    }
  }

  function tryAgain() {
    if (attempt >= 3) return;
    setAttempt(a => a + 1);
    setPhotoUri(null);
    setScore(null);
    setScreen('camera');
  }

  async function shareScore() {
    if (!score || !challenge) return;
    const blocks = [1, 2, 3].map(i => {
      if (i < attempt) return '🟥';
      if (i === attempt) return score.correct ? '🟩' : '🟥';
      return '⬛';
    }).join('');
    const text = `📸 SnapIT\n${challenge.object_emoji} ${challenge.object_name}\n${blocks}  ${score.total_score.toLocaleString()} pts\n${score.speed_label} · ${score.framing_label}\nsnapit.app`;
    await Share.share({ message: text });
  }

  const diffColor = (d: string) => d === 'easy' ? C.green : d === 'medium' ? C.yellow : C.red;
  const diffLabel = (d: string) => d === 'easy' ? t('play.easy') : d === 'medium' ? t('play.medium') : t('play.hard');
  const fmtTime   = (s: number) => `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;

  // ── Done ────────────────────────────────────────────────────────────────────
  if (screen === 'done') return (
    <ScrollView style={styles.root} contentContainerStyle={styles.center}>
      <WeekCalendar week={week} />
      <View style={styles.doneCard}>
        <Text style={styles.doneIcon}>🎯</Text>
        <Text style={styles.doneTitle}>{t('play.doneTitle')}</Text>
        <Text style={styles.doneSub}>{t('play.doneSub')}</Text>
      </View>
    </ScrollView>
  );

  // ── Camera ──────────────────────────────────────────────────────────────────
  if (screen === 'camera') return (
    <View style={{ flex: 1, backgroundColor: '#000' }}>
      <CameraView ref={cameraRef} style={{ flex: 1 }} facing="back">
        <View style={styles.cameraOverlay}>
          {challenge && (
            <View style={styles.cameraTarget}>
              <Text style={styles.cameraTargetText}>
                {t('play.photographTarget', { emoji: challenge.object_emoji, name: challenge.object_name })}
              </Text>
            </View>
          )}
          <View style={styles.focusRing} />
          <AttemptsRow attempt={attempt} score={null} />
          <TouchableOpacity style={styles.snapBtn} onPress={takePhoto}>
            <View style={styles.snapBtnInner} />
          </TouchableOpacity>
        </View>
      </CameraView>
    </View>
  );

  // ── Preview ─────────────────────────────────────────────────────────────────
  if (screen === 'preview' && photoUri) return (
    <View style={{ flex: 1, backgroundColor: '#000' }}>
      <Image source={{ uri: photoUri }} style={{ flex: 1 }} resizeMode="cover" />
      <View style={styles.previewActions}>
        <TouchableOpacity style={[S.btnSecondary, { flex: 1, marginBottom: 0, marginRight: 8 }]}
          onPress={() => setScreen('camera')}>
          <Text style={S.btnText}>{t('play.retake')}</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[S.btnPrimary, { flex: 1, marginBottom: 0 }]}
          onPress={submitPhoto} disabled={loading}>
          {loading
            ? <ActivityIndicator color="#fff" />
            : <Text style={S.btnText}>{t('play.useThis')}</Text>}
        </TouchableOpacity>
      </View>
    </View>
  );

  // ── Score ────────────────────────────────────────────────────────────────────
  if (screen === 'score' && score && challenge) return (
    <ScrollView style={styles.root} contentContainerStyle={{ padding: 16 }}>
      {/* Hero */}
      <View style={[styles.scoreHero, { borderColor: score.correct ? C.green : C.red }]}>
        <Text style={styles.scoreIcon}>{score.correct ? '🎯' : '❌'}</Text>
        <Text style={[styles.scoreTotal, { color: score.correct ? C.green : C.red }]}>
          {score.total_score.toLocaleString()}
        </Text>
        <Text style={styles.scoreLabel}>{score.correct ? t('play.correctLabel') : t('play.wrongLabel')}</Text>
        <Text style={styles.scoreConf}>
          {score.correct
            ? t('play.confidenceLabel', { pct: score.confidence_pct })
            : t('play.wrongDetected', { detected: score.detected_class, object: challenge.object_name })}
        </Text>
      </View>

      {/* Annotated image */}
      {score.annotated_image_b64 && (
        <Image
          source={{ uri: `data:image/jpeg;base64,${score.annotated_image_b64}` }}
          style={styles.annotated}
          resizeMode="contain"
        />
      )}

      {/* Breakdown */}
      <Text style={[S.sectionTitle, { marginTop: 8 }]}>{t('play.breakdown')}</Text>
      <View style={styles.breakdownGrid}>
        <BreakdownItem label={t('play.baseScore')}  value={score.base_score.toLocaleString()} color={C.text} />
        <BreakdownItem label={t('play.speed')}      value={`+${score.speed_bonus}`}   color={C.green}  sub={score.speed_label} />
        <BreakdownItem label={t('play.framing')}    value={`+${score.framing_bonus}`} color={C.green}  sub={score.framing_label} />
        <BreakdownItem label={t('play.clutter')}    value={`-${score.clutter_penalty}`} color={C.red} />
        {score.attempt_penalty > 0 &&
          <BreakdownItem label={t('play.attemptN', { n: score.attempt_number })} value={`-${score.attempt_penalty}`} color={C.red} />}
        <BreakdownItem label={t('play.difficulty')} value={`×${score.difficulty_mult}`} color={C.accent} />
      </View>

      {/* Buttons */}
      <AttemptsRow attempt={attempt} score={score} />
      <View style={{ flexDirection: 'row', gap: 10, marginTop: 16 }}>
        {!score.correct && attempt < 3 && (
          <TouchableOpacity style={[S.btnPrimary, { flex: 1, marginBottom: 0 }]} onPress={tryAgain}>
            <Text style={S.btnText}>{t('play.tryAgain', { n: attempt + 1 })}</Text>
          </TouchableOpacity>
        )}
        <TouchableOpacity style={[S.btnSecondary, { flex: 1, marginBottom: 0 }]} onPress={shareScore}>
          <Text style={S.btnText}>{t('play.share')}</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );

  // ── Challenge ────────────────────────────────────────────────────────────────
  return (
    <ScrollView style={styles.root} contentContainerStyle={{ padding: 16 }}>
      <WeekCalendar week={week} />

      {!challenge ? (
        <View style={styles.center}><ActivityIndicator color={C.accent} size="large" /></View>
      ) : (
        <>
          {/* Challenge card */}
          <View style={styles.challengeCard}>
            <Text style={styles.challengeDate}>
              {new Date(challenge.date).toLocaleDateString(i18nInstance.language, { day: 'numeric', month: 'long' })} · {challenge.weekday}
            </Text>
            <Text style={styles.challengeEmoji}>{challenge.object_emoji}</Text>
            <Text style={styles.challengeName}>{challenge.object_name}</Text>
            <View style={[styles.diffBadge, { backgroundColor: diffColor(challenge.difficulty) + '22', borderColor: diffColor(challenge.difficulty) + '55' }]}>
              <Text style={[styles.diffText, { color: diffColor(challenge.difficulty) }]}>{diffLabel(challenge.difficulty)}</Text>
            </View>
            {challenge.hint && <Text style={styles.challengeHint}>💡 {challenge.hint}</Text>}
            <Text style={styles.challengePts}>{t('play.basePts', { pts: challenge.base_points.toLocaleString() })}</Text>
          </View>

          {/* Timer */}
          <View style={styles.timerCard}>
            <Text style={S.muted}>{t('play.timer')}</Text>
            <Text style={styles.timerValue}>{fmtTime(elapsed)}</Text>
          </View>

          <TouchableOpacity style={S.btnPrimary} onPress={openCamera}>
            <Text style={S.btnText}>{t('play.takePhoto')}</Text>
          </TouchableOpacity>
        </>
      )}
    </ScrollView>
  );
}

// ── Sub-components ────────────────────────────────────────────────────────────

function WeekCalendar({ week }: { week: WeekDay[] }) {
  const { t } = useTranslation();
  if (!week.length) return null;
  const diffColor = (d: string) => d === 'easy' ? C.green : d === 'medium' ? C.yellow : C.red;
  const diffShort = (d: string) => d === 'easy' ? t('difficulty.easy') : d === 'medium' ? t('difficulty.medium') : t('difficulty.hard');
  return (
    <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginBottom: 16 }}>
      {week.map(d => (
        <View key={d.date} style={[styles.weekDay, d.is_today && styles.weekDayToday]}>
          <Text style={styles.weekDayName}>{d.weekday.slice(0, 3).toUpperCase()}</Text>
          <Text style={styles.weekDayEmoji}>{d.object_emoji}</Text>
          <Text style={[styles.weekDayDiff, { color: diffColor(d.difficulty) }]}>{diffShort(d.difficulty)}</Text>
        </View>
      ))}
    </ScrollView>
  );
}

function AttemptsRow({ attempt, score }: { attempt: number; score: ScoreResult | null }) {
  return (
    <View style={styles.attemptsRow}>
      {[1, 2, 3].map(i => {
        let bg: string = C.border;
        if (i < attempt) bg = score?.correct ? C.accent : C.red;
        else if (i === attempt) bg = C.accent;
        return <View key={i} style={[styles.attemptDot, { backgroundColor: bg }]} />;
      })}
    </View>
  );
}

function BreakdownItem({ label, value, color, sub }: { label: string; value: string; color: string; sub?: string }) {
  return (
    <View style={styles.breakdownItem}>
      <Text style={styles.breakdownLabel}>{label}</Text>
      <Text style={[styles.breakdownValue, { color }]}>{value}</Text>
      {sub && <Text style={styles.breakdownSub}>{sub}</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  root:           { flex: 1, backgroundColor: C.bg },
  center:         { alignItems: 'center', justifyContent: 'center', padding: 24 },
  challengeCard:  { backgroundColor: '#1a1a30', borderWidth: 1, borderColor: C.accent, borderRadius: 16, padding: 24, alignItems: 'center', marginBottom: 12 },
  challengeDate:  { fontSize: 11, color: C.muted, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 },
  challengeEmoji: { fontSize: 72, marginVertical: 8 },
  challengeName:  { fontSize: 26, fontWeight: '800', color: C.text, marginBottom: 6 },
  diffBadge:      { borderWidth: 1, borderRadius: 20, paddingHorizontal: 14, paddingVertical: 4, marginBottom: 10 },
  diffText:       { fontSize: 12, fontWeight: '700', textTransform: 'uppercase' },
  challengeHint:  { fontSize: 13, color: C.muted, marginTop: 4 },
  challengePts:   { fontSize: 13, color: C.accent, marginTop: 8, fontWeight: '600' },
  timerCard:      { ...S.card, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  timerValue:     { fontSize: 22, fontWeight: '800', color: C.yellow, fontVariant: ['tabular-nums'] },
  cameraOverlay:  { flex: 1, justifyContent: 'space-between', paddingBottom: 40 },
  cameraTarget:   { margin: 16, marginTop: 60, backgroundColor: 'rgba(124,109,255,0.3)', borderWidth: 1, borderColor: C.accent, borderRadius: 10, padding: 10, alignItems: 'center' },
  cameraTargetText: { color: '#fff', fontWeight: '700', fontSize: 14 },
  focusRing:      { width: 80, height: 80, borderRadius: 40, borderWidth: 2, borderColor: 'rgba(255,255,255,0.4)', alignSelf: 'center' },
  snapBtn:        { width: 72, height: 72, borderRadius: 36, backgroundColor: 'rgba(255,255,255,0.3)', alignSelf: 'center', alignItems: 'center', justifyContent: 'center' },
  snapBtnInner:   { width: 60, height: 60, borderRadius: 30, backgroundColor: '#fff' },
  attemptsRow:    { flexDirection: 'row', gap: 8, justifyContent: 'center', marginVertical: 12 },
  attemptDot:     { width: 10, height: 10, borderRadius: 5 },
  previewActions: { flexDirection: 'row', padding: 16, paddingBottom: 32, backgroundColor: C.bg, gap: 10 },
  scoreHero:      { borderWidth: 1, borderRadius: 16, padding: 24, alignItems: 'center', marginBottom: 16 },
  scoreIcon:      { fontSize: 48, marginBottom: 8 },
  scoreTotal:     { fontSize: 52, fontWeight: '900', letterSpacing: -2 },
  scoreLabel:     { fontSize: 14, color: C.muted, marginTop: 4 },
  scoreConf:      { fontSize: 13, color: C.accent, marginTop: 6, fontWeight: '600', textAlign: 'center' },
  annotated:      { width: '100%', height: 220, borderRadius: 12, marginBottom: 16 },
  breakdownGrid:  { flexDirection: 'row', flexWrap: 'wrap', gap: 10, marginBottom: 8 },
  breakdownItem:  { width: '47%', backgroundColor: C.card, borderWidth: 1, borderColor: C.border, borderRadius: 12, padding: 14 },
  breakdownLabel: { fontSize: 11, color: C.muted, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 4 },
  breakdownValue: { fontSize: 20, fontWeight: '800' },
  breakdownSub:   { fontSize: 11, color: C.muted, marginTop: 2 },
  weekDay:        { backgroundColor: C.surface, borderWidth: 1, borderColor: C.border as string, borderRadius: 10, padding: 10, alignItems: 'center' as const, marginRight: 8, minWidth: 58 },
  weekDayToday:   { borderColor: C.accent as string, backgroundColor: 'rgba(124,109,255,0.1)' },
  weekDayName:    { fontSize: 10, color: C.muted, marginBottom: 4 },
  weekDayEmoji:   { fontSize: 22, marginBottom: 2 },
  weekDayDiff:    { fontSize: 9, fontWeight: '700', textTransform: 'uppercase' },
  doneCard:       { backgroundColor: 'rgba(74,222,128,0.08)', borderWidth: 1, borderColor: 'rgba(74,222,128,0.3)', borderRadius: 16, padding: 32, alignItems: 'center' },
  doneIcon:       { fontSize: 56, marginBottom: 10 },
  doneTitle:      { fontSize: 18, fontWeight: '800', color: C.green, textAlign: 'center' },
  doneSub:        { fontSize: 13, color: C.muted, marginTop: 6 },
});

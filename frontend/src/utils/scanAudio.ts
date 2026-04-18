export type ScanAudioType = "success" | "error";

type BrowserAudioContext = Window & {
  webkitAudioContext?: typeof AudioContext;
};

let audioContext: AudioContext | null = null;

const getAudioContext = (): AudioContext | null => {
  if (typeof window === "undefined") {
    return null;
  }

  if (audioContext) {
    return audioContext;
  }

  const AudioContextConstructor =
    window.AudioContext || (window as BrowserAudioContext).webkitAudioContext;
  if (!AudioContextConstructor) {
    return null;
  }

  audioContext = new AudioContextConstructor();
  return audioContext;
};

export const playScanAudio = (type: ScanAudioType): void => {
  const context = getAudioContext();
  if (!context) {
    return;
  }

  const now = context.currentTime;
  if (context.state === "suspended") {
    void context.resume();
  }

  const oscillator = context.createOscillator();
  const gainNode = context.createGain();
  let stopAt = now + 0.13;

  if (type === "success") {
    oscillator.frequency.setValueAtTime(880, now);
    oscillator.frequency.linearRampToValueAtTime(1046, now + 0.08);
    gainNode.gain.setValueAtTime(0.0001, now);
    gainNode.gain.exponentialRampToValueAtTime(0.08, now + 0.01);
    gainNode.gain.exponentialRampToValueAtTime(0.0001, now + 0.12);
    stopAt = now + 0.13;
  } else {
    oscillator.frequency.setValueAtTime(220, now);
    oscillator.frequency.linearRampToValueAtTime(160, now + 0.12);
    gainNode.gain.setValueAtTime(0.0001, now);
    gainNode.gain.exponentialRampToValueAtTime(0.09, now + 0.02);
    gainNode.gain.exponentialRampToValueAtTime(0.0001, now + 0.16);
    stopAt = now + 0.17;
  }

  oscillator.connect(gainNode);
  gainNode.connect(context.destination);
  oscillator.start(now);
  oscillator.stop(stopAt);
};

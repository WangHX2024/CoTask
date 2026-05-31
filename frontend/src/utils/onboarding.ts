import { ONBOARDING_VERSION, type OnboardingPrefs } from '@/constants/onboarding'

export function getOnboardingPrefs(prefs?: Record<string, unknown> | null): OnboardingPrefs {
  const raw = prefs?.onboarding
  if (!raw || typeof raw !== 'object') return {}
  return raw as OnboardingPrefs
}

export function isOnboardingCompleted(prefs?: Record<string, unknown> | null): boolean {
  const ob = getOnboardingPrefs(prefs)
  return ob.completed === true && (ob.version ?? 0) >= ONBOARDING_VERSION
}

export function buildOnboardingCompletedPrefs(
  oldPrefs?: Record<string, unknown> | null,
): Record<string, unknown> {
  return {
    ...(oldPrefs || {}),
    onboarding: {
      completed: true,
      version: ONBOARDING_VERSION,
      completed_at: new Date().toISOString(),
    },
  }
}

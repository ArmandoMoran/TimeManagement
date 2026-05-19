// localStorage-backed token storage. Acceptable for an internal SPA;
// if XSS is a concern, swap to httpOnly cookies later.

const ACCESS_KEY = "timetrack.access_token";
const REFRESH_KEY = "timetrack.refresh_token";

type Listener = () => void;
const listeners = new Set<Listener>();

function notify(): void {
  for (const l of listeners) l();
}

export const tokenStore = {
  getAccessToken(): string | null {
    return localStorage.getItem(ACCESS_KEY);
  },
  getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_KEY);
  },
  setTokens(access: string, refresh: string): void {
    localStorage.setItem(ACCESS_KEY, access);
    localStorage.setItem(REFRESH_KEY, refresh);
    notify();
  },
  clear(): void {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
    notify();
  },
  subscribe(listener: Listener): () => void {
    listeners.add(listener);
    return () => {
      listeners.delete(listener);
    };
  },
};

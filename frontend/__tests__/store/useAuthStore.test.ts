import { renderHook, act } from '@testing-library/react';
import { useAuthStore } from '@/store/useAuthStore';

describe('useAuthStore', () => {
  beforeEach(() => {
    // Clear localStorage and reset store before each test
    window.localStorage.clear();
    const store = useAuthStore.getState();
    act(() => {
      store.logout();
    });
  });

  it('initializes with default unauthenticated state', () => {
    const { result } = renderHook(() => useAuthStore());
    
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
  });

  it('updates state and localStorage on login', () => {
    const { result } = renderHook(() => useAuthStore());
    
    const mockUser = { id: '1', email: 'test@example.com', full_name: 'Test User' };
    
    act(() => {
      result.current.login('fake-token', mockUser);
    });
    
    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user).toEqual(mockUser);
    expect(window.localStorage.getItem('auth_token')).toBe('fake-token');
    expect(window.localStorage.getItem('auth_user')).toEqual(JSON.stringify(mockUser));
  });

  it('clears state and localStorage on logout', () => {
    const { result } = renderHook(() => useAuthStore());
    
    const mockUser = { id: '1', email: 'test@example.com', full_name: 'Test User' };
    
    act(() => {
      result.current.login('fake-token', mockUser);
    });
    
    act(() => {
      result.current.logout();
    });
    
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
    expect(window.localStorage.getItem('auth_token')).toBeNull();
    expect(window.localStorage.getItem('auth_user')).toBeNull();
  });
});

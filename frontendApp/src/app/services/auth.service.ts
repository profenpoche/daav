import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Router } from '@angular/router';
import { BehaviorSubject, Observable, throwError } from 'rxjs';
import { map, catchError, tap } from 'rxjs/operators';
import {
  User,
  Token,
  LoginRequest,
  RegisterRequest,
  ForgotPasswordRequest,
  ResetPasswordRequest,
  ChangePasswordRequest,
  UserUpdate
} from '../models/auth.models';
import { TokenService } from './token.service';
import { BaseService } from './base.service.service';

/**
 * Authentication Service
 * Handles all authentication-related operations
 */
@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private currentUserSubject: BehaviorSubject<User | null>;
  public currentUser$: Observable<User | null>;
  private refreshTokenInProgress = false;

  constructor(
    private http: HttpClient,
    private tokenService: TokenService,
    private baseService: BaseService,
    private router: Router
  ) {
    this.currentUserSubject = new BehaviorSubject<User | null>(null);
    this.currentUser$ = this.currentUserSubject.asObservable();
  }

  /**
   * Get current user value
   */
  get currentUserValue(): User | null {
    return this.currentUserSubject.value;
  }

  /**
   * Login user
   */
  login(username: string, password: string, rememberMe: boolean = false): Observable<Token> {
    const loginRequest: LoginRequest = { username, password };

    return this.http.post<Token>(`${this.baseService.urlBack}/auth/login`, loginRequest)
      .pipe(
        tap(async (token) => {
          // Save tokens
          await this.tokenService.saveTokens(token.access_token, token.refresh_token, rememberMe);

          // Load user info
          await this.loadCurrentUser();
        }),
        catchError(this.handleError)
      );
  }

  /**
   * Register new user
   */
  register(registerData: RegisterRequest): Observable<User> {
    return this.http.post<User>(`${this.baseService.urlBack}/auth/register`, registerData)
      .pipe(
        catchError(this.handleError)
      );
  }

  /**
   * Logout user
   */
  async logout(): Promise<void> {
    await this.tokenService.clearTokens();
    this.currentUserSubject.next(null);
    // Navigate to login page
    this.router.navigate(['/login'], { replaceUrl: true });
  }

  /**
   * Refresh access token
   */
  async refreshToken(): Promise<string | null> {
    if (this.refreshTokenInProgress) {
      // Wait for ongoing refresh
      return new Promise((resolve) => {
        const interval = setInterval(async () => {
          if (!this.refreshTokenInProgress) {
            clearInterval(interval);
            resolve(this.tokenService.getAccessToken());
          }
        }, 100);
      });
    }

    this.refreshTokenInProgress = true;

    try {
      const refreshToken = await this.tokenService.getRefreshToken();

      if (!refreshToken) {
        this.refreshTokenInProgress = false;
        return null;
      }

      const token = await this.http.post<Token>(`${this.baseService.urlBack}/auth/refresh`, {
        refresh_token: refreshToken
      }).toPromise();

      if (token) {
        const rememberMe = await this.tokenService.isRememberMe();
        await this.tokenService.saveTokens(token.access_token, token.refresh_token, rememberMe);
        this.refreshTokenInProgress = false;
        return token.access_token;
      }

      this.refreshTokenInProgress = false;
      return null;
    } catch (error) {
      this.refreshTokenInProgress = false;
      console.error('Token refresh failed:', error);
      await this.logout();
      return null;
    }
  }

  /**
   * Load current user info
   */
  async loadCurrentUser(): Promise<void> {
    try {
      const accessToken = this.tokenService.getAccessToken();

      if (!accessToken) {
        this.currentUserSubject.next(null);
        return;
      }

      const headers = new HttpHeaders({
        'Authorization': `Bearer ${accessToken}`
      });

      const user = await this.http.get<User>(`${this.baseService.urlBack}/auth/me`, { headers }).toPromise();

      if (user) {
        this.currentUserSubject.next(user);
      }
    } catch (error) {
      console.error('Failed to load current user:', error);
      this.currentUserSubject.next(null);
    }
  }

  /**
   * Check if user is authenticated
   */
  async isAuthenticated(): Promise<boolean> {
    const hasTokens = await this.tokenService.hasTokens();

    if (!hasTokens) {
      return false;
    }

    // Try to refresh token if needed
    const accessToken = this.tokenService.getAccessToken();
    if (!accessToken || this.tokenService.isTokenExpired(accessToken)) {
      const newToken = await this.refreshToken();
      return !!newToken;
    }

    return true;
  }

  /**
   * Check if user is admin
   */
  isAdmin(): boolean {
    const user = this.currentUserValue;
    return user?.role === 'admin';
  }

  /**
   * Forgot password - Send reset email
   */
  forgotPassword(email: string): Observable<{ message: string }> {
    const request: ForgotPasswordRequest = { email };

    return this.http.post<{ message: string }>(`${this.baseService.urlBack}/auth/forgot-password`, request)
      .pipe(
        catchError(this.handleError)
      );
  }

  /**
   * Reset password with token
   */
  resetPassword(token: string, newPassword: string): Observable<{ message: string }> {
    const request: ResetPasswordRequest = { token, new_password: newPassword };

    return this.http.post<{ message: string }>(`${this.baseService.urlBack}/auth/reset-password`, request)
      .pipe(
        catchError(this.handleError)
      );
  }

  /**
   * Change password (authenticated user)
   */
  changePassword(currentPassword: string, newPassword: string): Observable<{ message: string }> {
    const request: ChangePasswordRequest = { current_password: currentPassword, new_password: newPassword };
    const accessToken = this.tokenService.getAccessToken();

    const headers = new HttpHeaders({
      'Authorization': `Bearer ${accessToken}`
    });

    return this.http.post<{ message: string }>(`${this.baseService.urlBack}/auth/change-password`, request, { headers })
      .pipe(
        catchError(this.handleError)
      );
  }

  /**
   * Update current user profile
   */
  updateProfile(userData: UserUpdate): Observable<User> {
    const accessToken = this.tokenService.getAccessToken();

    const headers = new HttpHeaders({
      'Authorization': `Bearer ${accessToken}`
    });

    return this.http.put<User>(`${this.baseService.urlBack}/auth/me`, userData, { headers })
      .pipe(
        tap((user) => {
          this.currentUserSubject.next(user);
        }),
        catchError(this.handleError)
      );
  }

  /**
   * Auto-refresh token timer
   * Call this on app initialization
   */
  startTokenRefreshTimer(): void {
    // Check every minute if token needs refresh
    setInterval(async () => {
      if (this.tokenService.shouldRefreshToken()) {
        await this.refreshToken();
      }
    }, 60000); // 1 minute
  }

  /**
   * Handle HTTP errors
   */
  private handleError(error: any): Observable<never> {
    let errorMessage = 'An error occurred';

    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorMessage = `Error: ${error.error.message}`;
    } else {
      // Server-side error
      errorMessage = error.error?.detail || error.message || 'Server error';
    }

    console.error('Auth Service Error:', errorMessage);
    return throwError(() => new Error(errorMessage));
  }
}

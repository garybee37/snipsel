<script lang="ts">
  import { api, type Collection } from '../lib/api';
  import { currentUser } from '../lib/session';
  import { collectionAnchor, currentView } from '../lib/stores';
  import {
    checkPushSubscription,
    subscribeToPushNotifications,
    unsubscribeFromPushNotifications,
  } from '../lib/pushManager';
  import { startRegistration } from '@simplewebauthn/browser';

  const DEFAULT_ACCENT = '#4f46e5';
  type Rgb = { r: number; g: number; b: number };

  let defaultHeaderColor = $state('');
  let templateCollections = $state<Collection[]>([]);
  let dayTemplateId = $state<string>('');
  let isBusy = $state(false);
  let showPasscodeForm = $state(false);
  let passcode = $state('');
  let passwordConfirm = $state('');
  let passcodeError = $state('');
  let hasPushEnabled = $state(false);

  let isOtpSetupActive = $state(false);
  let otpSecret = $state('');
  let otpProvisioningUrl = $state('');
  let otpCodeInput = $state('');
  let otpSetupError = $state('');
  let securityError = $state('');

  let passkeys = $state<import('../lib/api').UserPasskey[]>([]);
  let isPasskeyAddActive = $state(false);
  let newPasskeyName = $state('');
  let passkeyError = $state('');
  
  let newEmail = $state('');
  let newPassword = $state('');
  let currentPasswordConfirm = $state('');
  let accountUpdateError = $state('');
  let accountUpdateSuccess = $state('');
  let showAccountForm = $state(false);


  async function startOtpSetup() {
    isBusy = true;
    otpSetupError = '';
    try {
      const res = await api.twoFactor.generate();
      otpSecret = res.secret;
      otpProvisioningUrl = res.provisioning_url;
      isOtpSetupActive = true;
    } catch (e: any) {
      otpSetupError = e.error?.message || 'Failed to initiate 2FA';
    } finally {
      isBusy = false;
    }
  }

  async function enableOtp() {
    if (!otpCodeInput || !passwordConfirm) return;
    isBusy = true;
    otpSetupError = '';
    try {
      await api.twoFactor.enable({ code: otpCodeInput, password_confirm: passwordConfirm });
      const res = await api.me();
      currentUser.set(res.user);
      isOtpSetupActive = false;
      otpCodeInput = '';
      passwordConfirm = '';
    } catch (e: any) {
      otpSetupError = e.error?.message || 'Failed to enable 2FA';
    } finally {
      isBusy = false;
    }
  }

  async function disableOtp(pass: string) {
    isBusy = true;
    securityError = '';
    try {
      await api.twoFactor.disable(pass);
      const res = await api.me();
      currentUser.set(res.user);
    } catch (e: any) {
      securityError = e.error?.message || 'Failed to disable 2FA';
    } finally {
      isBusy = false;
    }
  }

  async function loadPasskeys() {
    try {
      const res = await api.passkeys.list();
      passkeys = res.passkeys;
    } catch (err) {
      console.error('Failed to load passkeys', err);
    }
  }

  async function addPasskey() {
    if (!newPasskeyName) return;
    isBusy = true;
    passkeyError = '';
    try {
      const options = await api.passkeys.registerBegin();
      const attResp = await startRegistration(options);
      await api.passkeys.registerComplete(attResp, newPasskeyName);
      
      await loadPasskeys();
      const meRes = await api.me();
      currentUser.set(meRes.user);
      isPasskeyAddActive = false;
      newPasskeyName = '';
    } catch (e: any) {
      console.error(e);
      passkeyError = e.error?.message || e.message || 'Failed to register passkey';
    } finally {
      isBusy = false;
    }
  }

  async function removePasskey(id: string) {
    if (!confirm('Are you sure you want to remove this passkey?')) return;
    isBusy = true;
    try {
      await api.passkeys.delete(id);
      await loadPasskeys();
      const meRes = await api.me();
      currentUser.set(meRes.user);
    } catch (e: any) {
      alert(e.error?.message || 'Failed to delete passkey');
    } finally {
      isBusy = false;
    }
  }

  function clampByte(n: number): number {
    return Math.max(0, Math.min(255, Math.round(n)));
  }

  function hexToRgb(hex: string): Rgb | null {
    const h = hex.trim();
    const m = /^#([0-9a-fA-F]{6})$/.exec(h);
    if (!m) return null;
    const v = m[1];
    return {
      r: parseInt(v.slice(0, 2), 16),
      g: parseInt(v.slice(2, 4), 16),
      b: parseInt(v.slice(4, 6), 16),
    };
  }

  function mixRgb(a: Rgb, b: Rgb, t: number): Rgb {
    const tt = Math.max(0, Math.min(1, t));
    return {
      r: clampByte(a.r + (b.r - a.r) * tt),
      g: clampByte(a.g + (b.g - a.g) * tt),
      b: clampByte(a.b + (b.b - a.b) * tt),
    };
  }

  function rgba(c: Rgb, alpha: number): string {
    const a = Math.max(0, Math.min(1, alpha));
    return `rgba(${c.r}, ${c.g}, ${c.b}, ${a})`;
  }

  function getAccent(): string {
    const raw = ($currentUser?.default_collection_header_color || '').trim() || DEFAULT_ACCENT;
    return /^#[0-9a-fA-F]{6}$/.test(raw) ? raw : DEFAULT_ACCENT;
  }

  function getAccentTint(): string {
    const base = { r: 255, g: 255, b: 255 };
    const accent = hexToRgb(getAccent());
    const mixed = accent ? mixRgb(base, accent, 0.14) : base;
    return rgba(mixed, 0.96);
  }

  async function logout() {
    await api.logout();
    currentUser.set(null);
    collectionAnchor.set(null);
    currentView.set({ type: 'loading' });
  }

  async function saveDefaultHeaderColor() {
    isBusy = true;
    try {
      const v = defaultHeaderColor.trim() || null;
      const res = await api.updateMe({ default_collection_header_color: v });
      currentUser.set(res.user);
    } finally {
      isBusy = false;
    }
  }

  async function toggleCarryOver() {
    isBusy = true;
    try {
      const next = !Boolean($currentUser?.carry_over_open_tasks ?? true);
      const res = await api.updateMe({ carry_over_open_tasks: next });
      currentUser.set(res.user);
    } finally {
      isBusy = false;
    }
  }

  async function loadTemplates() {
    const res = await api.collections.list();
    templateCollections = res.collections.filter((c) => Boolean(c.is_template));
  }

  async function saveDayTemplate() {
    isBusy = true;
    try {
      const id = dayTemplateId.trim() || null;
      const res = await api.updateMe({ day_collection_template_id: id });
      currentUser.set(res.user);
    } finally {
      isBusy = false;
    }
  }

  async function savePasscode() {
    if (passcode.length < 4) {
      passcodeError = 'Passcode must be at least 4 digits';
      return;
    }
    isBusy = true;
    passcodeError = '';
    try {
      await api.passcode.set({ passcode, password_confirm: passwordConfirm });
      const res = await api.me();
      currentUser.set(res.user);
      showPasscodeForm = false;
      passcode = '';
      passwordConfirm = '';
    } catch (e: any) {
      passcodeError = e.error?.message || 'Failed to set passcode';
    } finally {
      isBusy = false;
    }
  }

  async function togglePush() {
    isBusy = true;
    try {
      if (hasPushEnabled) {
        await unsubscribeFromPushNotifications();
        hasPushEnabled = false;
      } else {
        await subscribeToPushNotifications();
        hasPushEnabled = true;
      }
    } catch (err: any) {
      alert(err.message || 'Failed to toggle push notifications');
    } finally {
      isBusy = false;
    }
  }

  async function updateAccount() {
    if (!newEmail && !newPassword) {
      accountUpdateError = 'Please enter a new email or password';
      return;
    }
    if (!currentPasswordConfirm) {
      accountUpdateError = 'Current password is required to save changes';
      return;
    }
    
    isBusy = true;
    accountUpdateError = '';
    accountUpdateSuccess = '';
    try {
      const res = await api.updateMe({
        email: newEmail || undefined,
        password: newPassword || undefined,
        current_password: currentPasswordConfirm
      });
      currentUser.set(res.user);
      accountUpdateSuccess = 'Account updated successfully';
      newEmail = '';
      newPassword = '';
      currentPasswordConfirm = '';
      showAccountForm = false;
    } catch (e: any) {
      accountUpdateError = e.error?.message || 'Failed to update account';
    } finally {
      isBusy = false;
    }
  }

  async function sendTestPush() {
    isBusy = true;
    try {
      await api.notifications.testPush();
    } catch (err: any) {
      alert(err.error?.message || 'Failed to send test notification');
    } finally {
      isBusy = false;
    }
  }

  $effect(() => {
    defaultHeaderColor = $currentUser?.default_collection_header_color ?? DEFAULT_ACCENT;
    dayTemplateId = $currentUser?.day_collection_template_id ?? '';
  });

  $effect(() => {
    loadTemplates();
  });

  $effect(() => {
    checkPushSubscription().then(v => hasPushEnabled = v);
  });
</script>

<div class="space-y-4">
  <h2 class="flex items-center gap-2 text-2xl font-semibold">
    <svg class="h-6 w-6 text-slate-700" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.72V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.17a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
    <span>Settings</span>
  </h2>

  <div class="space-y-3">
    <!-- Account -->
    <div class="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80 dark:ring-white/10">
      <div class="text-xs uppercase text-slate-500">Account</div>
      <div class="mt-3 flex items-center justify-between gap-4">
        <div class="min-w-0 flex-1">
          <div class="truncate text-lg font-medium text-slate-900 dark:text-slate-100">{$currentUser?.username}</div>
          <div class="truncate text-sm text-slate-500 dark:text-slate-400">{$currentUser?.email}</div>
        </div>
        <div class="flex gap-2">
            <button 
              class="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50 dark:border-white/10 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700" 
              type="button" 
              onclick={() => { showAccountForm = !showAccountForm; accountUpdateError = ''; accountUpdateSuccess = ''; }}
              disabled={isBusy}
            >
              {showAccountForm ? 'Cancel' : 'Edit'}
            </button>
            <button 
              class="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-red-600 shadow-sm ring-1 ring-black/5 hover:bg-red-50 disabled:opacity-50 dark:border-white/10 dark:bg-slate-800 dark:text-red-400 dark:hover:bg-red-950/30" 
              type="button" 
              onclick={logout}
              disabled={isBusy}
            >
              Logout
            </button>
        </div>
      </div>

      {#if showAccountForm}
        <div class="mt-4 space-y-4 border-t border-slate-100 pt-4 dark:border-white/5">
          <div>
            <label for="new-email" class="block text-sm font-medium text-slate-700 dark:text-slate-300">New Email Address (optional)</label>
            <input
              id="new-email"
              type="email"
              class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm ring-1 ring-black/5 focus:outline-none focus:ring-2 focus:ring-black/5 dark:border-white/10 dark:bg-slate-800 dark:text-white dark:focus:ring-white/10"
              bind:value={newEmail}
              placeholder="new.email@example.com"
            />
          </div>
          <div>
            <label for="new-password" class="block text-sm font-medium text-slate-700 dark:text-slate-300">New Password (optional, min 4 chars)</label>
            <input
              id="new-password"
              type="password"
              class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm ring-1 ring-black/5 focus:outline-none focus:ring-2 focus:ring-black/5 dark:border-white/10 dark:bg-slate-800 dark:text-white dark:focus:ring-white/10"
              bind:value={newPassword}
              placeholder="••••••••"
            />
          </div>
          <div class="rounded-lg bg-slate-50 p-3 dark:bg-white/5">
            <label for="account-password-confirm" class="block text-sm font-medium text-slate-700 dark:text-slate-300">Confirm Current Password to save</label>
            <input
              id="account-password-confirm"
              type="password"
              class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm ring-1 ring-black/5 focus:outline-none focus:ring-2 focus:ring-black/5 dark:border-white/10 dark:bg-slate-800 dark:text-white dark:focus:ring-white/10"
              bind:value={currentPasswordConfirm}
              placeholder="Your current password"
            />
          </div>
          
          {#if accountUpdateError}
            <div class="text-xs font-medium text-red-600 dark:text-red-400">{accountUpdateError}</div>
          {/if}
          {#if accountUpdateSuccess}
            <div class="text-xs font-medium text-green-600 dark:text-green-400">{accountUpdateSuccess}</div>
          {/if}
          
          <button
            class="w-full rounded-full px-4 py-2.5 text-sm font-semibold text-white shadow-sm disabled:opacity-50 transition-all dark:opacity-90"
            style={`background-color: ${getAccent()}`}
            type="button"
            onclick={updateAccount}
            disabled={isBusy || (!newEmail && !newPassword) || !currentPasswordConfirm}
          >
            Save Account Changes
          </button>
        </div>
      {/if}
    </div>

    <!-- Appearance -->
    <div class="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/60">
      <div class="text-xs uppercase text-slate-500">Appearance</div>
      
      <div class="mt-4">
        <label for="theme-select" class="block text-sm font-medium text-slate-700 dark:text-slate-300">Color Theme</label>
        <div class="mt-2 grid grid-cols-3 gap-2">
          {#each ['system', 'light', 'dark'] as t}
            <button
              class="rounded-lg border px-3 py-2 text-sm font-medium transition-all {$currentUser?.theme === t ? 'bg-slate-900 text-white border-slate-900 dark:bg-white dark:text-slate-900 dark:border-white' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50 dark:bg-slate-800 dark:text-slate-400 dark:border-slate-700 dark:hover:bg-slate-700'}"
              type="button"
              onclick={async () => {
                isBusy = true;
                try {
                  const res = await api.updateMe({ theme: t as any });
                  currentUser.set(res.user);
                } finally {
                  isBusy = false;
                }
              }}
              disabled={isBusy}
            >
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          {/each}
        </div>
      </div>

      <div class="mt-6">
        <label for="accent-color-picker" class="block text-sm font-medium text-slate-700 dark:text-slate-300">Default collection header color</label>
        <div class="mt-2 flex items-center gap-2">
          <div class="flex flex-1 items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 shadow-sm ring-1 ring-black/5 dark:border-slate-700 dark:bg-slate-800">
            <input id="accent-color-picker" class="h-8 w-8 cursor-pointer overflow-hidden rounded border-none bg-transparent" type="color" bind:value={defaultHeaderColor} />
            <input class="min-w-0 flex-1 border-none bg-transparent text-sm font-mono text-slate-700 focus:outline-none focus:ring-0 dark:text-slate-300" bind:value={defaultHeaderColor} />
          </div>
          <button
            class="rounded-full border border-slate-200 bg-white px-5 py-2.5 text-sm font-semibold shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50 dark:border-slate-700 dark:bg-slate-800 dark:hover:bg-slate-700"
            style={`color: ${getAccent()}`}
            type="button"
            onclick={saveDefaultHeaderColor}
            disabled={isBusy}
          >
            Save
          </button>
        </div>
      </div>
    </div>

    <!-- Day Template -->
    <div class="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80 dark:ring-white/10">
      <div class="text-xs uppercase text-slate-500">Day template</div>
      <div class="mt-3">
        <label for="day-template-select" class="block text-sm font-medium text-slate-700 dark:text-slate-300">Template for new daily collections</label>
        <div class="mt-2 flex items-center gap-2">
          <select 
            id="day-template-select"
            class="flex-1 rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm shadow-sm ring-1 ring-black/5 focus:outline-none focus:ring-2 focus:ring-black/5 dark:border-white/10 dark:bg-slate-800 dark:text-white dark:focus:ring-white/10" 
            bind:value={dayTemplateId}
          >
            <option value="">No template</option>
            {#each templateCollections as c (c.id)}
              <option value={c.id}>
                {c.icon} {c.title}
              </option>
            {/each}
          </select>
          <button
            class="rounded-full border border-slate-200 bg-white px-5 py-2.5 text-sm font-semibold shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50 dark:border-white/10 dark:bg-slate-800 dark:hover:bg-slate-700"
            style={`color: ${getAccent()}`}
            type="button"
            onclick={saveDayTemplate}
            disabled={isBusy}
          >
            Save
          </button>
        </div>
      </div>
    </div>

    <!-- Tasks -->
    <div class="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80 dark:ring-white/10">
      <div class="text-xs uppercase text-slate-500">Tasks</div>
      <div class="mt-3 flex items-center justify-between gap-4">
        <div>
          <div class="text-sm font-medium text-slate-900 dark:text-slate-100">Carry over open tasks</div>
          <div class="text-xs text-slate-500 dark:text-slate-400">Move unfinished tasks from the last 30 days into today.</div>
        </div>
        <button
          class="rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold transition-all hover:bg-slate-50 disabled:opacity-40 dark:border-white/10 dark:bg-slate-800 dark:hover:bg-slate-700"
          type="button"
          onclick={toggleCarryOver}
          disabled={isBusy}
          style={Boolean($currentUser?.carry_over_open_tasks ?? true) ? `border-color: ${getAccent()}; color: ${getAccent()}; background-color: ${getAccentTint()}` : undefined}
        >
          {Boolean($currentUser?.carry_over_open_tasks ?? true) ? 'On' : 'Off'}
        </button>
      </div>
    </div>

    <!-- Notifications -->
    <div class="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80 dark:ring-white/10">
      <div class="text-xs uppercase text-slate-500">Notifications</div>
      <div class="mt-3 flex items-center justify-between gap-4">
        <div>
          <div class="text-sm font-medium text-slate-900 dark:text-slate-100">Push Notifications</div>
          <div class="text-xs text-slate-500 dark:text-slate-400">Receive alerts on this device for reminders.</div>
        </div>
        <button
          class="rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold transition-all hover:bg-slate-50 disabled:opacity-40 dark:border-white/10 dark:bg-slate-800 dark:hover:bg-slate-700"
          type="button"
          onclick={togglePush}
          disabled={isBusy}
          style={hasPushEnabled ? `border-color: ${getAccent()}; color: ${getAccent()}; background-color: ${getAccentTint()}` : undefined}
        >
          {hasPushEnabled ? 'Enabled' : 'Disabled'}
        </button>
      </div>

      {#if hasPushEnabled}
        <div class="mt-3 flex items-center justify-end">
          <button
            class="text-xs font-medium text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 transition-colors flex items-center gap-1.5"
            type="button"
            onclick={sendTestPush}
            disabled={isBusy}
          >
            <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
              <path d="M8 7a4 4 0 1 1 8 0c0 4.99 2 6.7 2 6.7h-12s2-1.71 2-6.7" />
            </svg>
            Send Test Notification
          </button>
        </div>
      {/if}
    </div>

    <!-- Security -->
    <div class="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80 dark:ring-white/10">
      <div class="flex items-center gap-2 text-xs uppercase text-slate-500">
        <svg class="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
          <path d="M7 11V7a5 5 0 0 1 10 0v4" />
        </svg>
        <span>Security</span>
      </div>
      
      <!-- Passcode -->
      <div class="border-b border-slate-100 pb-4 dark:border-white/5">
        {#if !showPasscodeForm}
          <div class="mt-3 flex items-center justify-between gap-4">
            <div>
              <div class="text-sm font-medium text-slate-900 dark:text-slate-100">Personal Passcode</div>
              <div class="text-xs text-slate-500 dark:text-slate-400">
                {$currentUser?.passcode_set ? 'Passcode is active.' : 'Set a passcode to protect sensitive collections.'}
              </div>
            </div>
            <button
              class="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50 transition-all dark:border-white/10 dark:bg-slate-800 dark:hover:bg-slate-700"
              style={`color: ${getAccent()}`}
              type="button"
              onclick={() => { showPasscodeForm = true; passcodeError = ''; }}
              disabled={isBusy}
            >
              {$currentUser?.passcode_set ? 'Change' : 'Set Passcode'}
            </button>
          </div>
        {:else}
          <div class="mt-4 space-y-4 transition-all">
            <div>
              <label for="new-passcode" class="block text-sm font-medium text-slate-700 dark:text-slate-300">New 4-digit passcode</label>
              <input
                id="new-passcode"
                type="password"
                inputmode="numeric"
                maxlength="12"
                class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm ring-1 ring-black/5 focus:outline-none focus:ring-2 focus:ring-black/5 dark:border-white/10 dark:bg-slate-800 dark:text-white dark:focus:ring-white/10"
                bind:value={passcode}
                oninput={(e) => passcode = e.currentTarget.value.replace(/\D/g, '')}
                placeholder="••••"
              />
            </div>
            <div>
              <label for="password-confirm" class="block text-sm font-medium text-slate-700 dark:text-slate-300">Confirm account password</label>
              <input
                id="password-confirm"
                type="password"
                class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm ring-1 ring-black/5 focus:outline-none focus:ring-2 focus:ring-black/5 dark:border-white/10 dark:bg-slate-800 dark:text-white dark:focus:ring-white/10"
                bind:value={passwordConfirm}
                placeholder="Your account password"
              />
            </div>
            
            {#if passcodeError}
              <div class="text-xs font-medium text-red-600 dark:text-red-400">{passcodeError}</div>
            {/if}
            
            <div class="flex items-center gap-2 pt-2">
              <button
                class="flex-1 rounded-full px-4 py-2.5 text-sm font-semibold text-white shadow-sm disabled:opacity-50 transition-all dark:opacity-90"
                style={`background-color: ${getAccent()}`}
                type="button"
                onclick={savePasscode}
                disabled={isBusy || passcode.length < 4 || !passwordConfirm}
              >
                Save Passcode
              </button>
              <button
                class="flex-1 rounded-full border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50 transition-all dark:border-white/10 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                type="button"
                onclick={() => { showPasscodeForm = false; passcode = ''; passwordConfirm = ''; }}
                disabled={isBusy}
              >
                Cancel
              </button>
            </div>
          </div>
        {/if}
      </div>

      <!-- Two-Factor Authentication -->
      <div class="border-b border-slate-100 py-4 dark:border-white/5">
        <div class="flex items-center justify-between gap-4">
          <div>
            <div class="text-sm font-medium text-slate-900 dark:text-slate-100">Two-Factor Authentication (OTP)</div>
            <div class="text-xs text-slate-500 dark:text-slate-400">
              {$currentUser?.otp_enabled ? 'Active. Extra security for your account.' : 'Enhance security by requiring a code from an authenticator app.'}
            </div>
          </div>
          {#if $currentUser?.otp_enabled}
            <button
              class="rounded-full border border-red-200 bg-white px-4 py-2 text-sm font-semibold text-red-600 shadow-sm ring-1 ring-black/5 hover:bg-red-50 disabled:opacity-50 dark:border-red-900/30 dark:bg-slate-800 dark:text-red-400"
              type="button"
              onclick={() => {
                const pass = prompt('Confirm password to disable 2FA:');
                if (pass) {
                  disableOtp(pass);
                }
              }}
              disabled={isBusy}
            >
              Disable
            </button>
          {:else}
            <button
              class="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50 transition-all dark:border-white/10 dark:bg-slate-800 dark:hover:bg-slate-700"
              style={`color: ${getAccent()}`}
              type="button"
              onclick={startOtpSetup}
              disabled={isBusy}
            >
              Set up 2FA
            </button>
          {/if}
        </div>

        {#if isOtpSetupActive}
          <div class="mt-4 space-y-4 rounded-xl bg-slate-50 p-4 dark:bg-white/5">
            <div class="text-sm font-medium">Scan this QR code in your app</div>
            <div class="flex justify-center rounded-lg bg-white p-2">
              <img src={`/api/auth/2fa/qr?provisioning_url=${encodeURIComponent(otpProvisioningUrl)}`} alt="2FA QR Code" class="h-48 w-48" />
            </div>
            <div class="text-xs text-slate-500 text-center">
              Or enter manually: <code class="bg-slate-200 px-1 dark:bg-white/10">{otpSecret}</code>
            </div>
            
            <div class="space-y-3">
              <div>
                <label for="otp-code" class="block text-sm font-medium text-slate-700 dark:text-slate-300">Enter code from app</label>
                <input
                  id="otp-code"
                  type="text"
                  inputmode="numeric"
                  maxlength="6"
                  class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:outline-none dark:border-white/10 dark:bg-slate-800"
                  bind:value={otpCodeInput}
                  placeholder="000000"
                />
              </div>
              <div>
                <label for="otp-password-confirm" class="block text-sm font-medium text-slate-700 dark:text-slate-300">Confirm account password</label>
                <input
                  id="otp-password-confirm"
                  type="password"
                  class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:outline-none dark:border-white/10 dark:bg-slate-800"
                  bind:value={passwordConfirm}
                  placeholder="Your account password"
                />
              </div>
            </div>

            {#if otpSetupError}
              <div class="text-xs font-medium text-red-600 dark:text-red-400">{otpSetupError}</div>
            {/if}

            <div class="flex gap-2">
              <button
                class="flex-1 rounded-full px-4 py-2 text-sm font-semibold text-white shadow-sm disabled:opacity-50"
                style={`background-color: ${getAccent()}`}
                type="button"
                onclick={enableOtp}
                disabled={isBusy || otpCodeInput.length < 6 || !passwordConfirm}
              >
                Enable 2FA
              </button>
              <button
                class="flex-1 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-300"
                type="button"
                onclick={() => { isOtpSetupActive = false; otpCodeInput = ''; passwordConfirm = ''; }}
                disabled={isBusy}
              >
                Cancel
              </button>
            </div>
          </div>
        {/if}
      </div>

      <!-- Passkeys -->
      <div class="mt-4">
        <div class="flex items-center justify-between gap-4">
          <div>
            <div class="text-sm font-medium text-slate-900 dark:text-slate-100">Passkeys</div>
            <div class="text-xs text-slate-500 dark:text-slate-400">
              Use biometric or hardware keys to log in without a password.
            </div>
          </div>
          <button
            class="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50 transition-all dark:border-white/10 dark:bg-slate-800 dark:hover:bg-slate-700"
            style={`color: ${getAccent()}`}
            type="button"
            onclick={() => { isPasskeyAddActive = true; passkeyError = ''; loadPasskeys(); }}
            disabled={isBusy}
          >
            Add Key
          </button>
        </div>

        {#if isPasskeyAddActive}
          <div class="mt-4 space-y-4 rounded-xl bg-slate-50 p-4 dark:bg-white/5">
            <div>
              <label for="passkey-name" class="block text-sm font-medium text-slate-700 dark:text-slate-300">Key Name</label>
              <input
                id="passkey-name"
                type="text"
                class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:outline-none dark:border-white/10 dark:bg-slate-800"
                bind:value={newPasskeyName}
                placeholder="e.g. MacBook Air, YubiKey"
              />
            </div>
            
            {#if passkeyError}
              <div class="text-xs font-medium text-red-600 dark:text-red-400">{passkeyError}</div>
            {/if}

            <div class="flex gap-2">
              <button
                class="flex-1 rounded-full px-4 py-2 text-sm font-semibold text-white shadow-sm disabled:opacity-50"
                style={`background-color: ${getAccent()}`}
                type="button"
                onclick={addPasskey}
                disabled={isBusy || !newPasskeyName}
              >
                Continue
              </button>
              <button
                class="flex-1 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-300"
                type="button"
                onclick={() => { isPasskeyAddActive = false; newPasskeyName = ''; }}
                disabled={isBusy}
              >
                Cancel
              </button>
            </div>
          </div>
        {/if}

        {#if passkeys.length > 0}
          <div class="mt-4 space-y-2">
            {#each passkeys as pk (pk.id)}
              <div class="flex items-center justify-between rounded-lg border border-slate-100 bg-white/50 px-3 py-2 dark:border-white/5 dark:bg-slate-900/50">
                <div class="flex items-center gap-2">
                  <svg class="h-4 w-4 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 2l-2 2" />
                    <circle cx="7" cy="15" r="5" />
                    <path d="M12 9l2 2" />
                    <path d="M16 5l2 2" />
                    <path d="M9 18l3 3" />
                  </svg>
                  <span class="text-sm font-medium">{pk.name}</span>
                </div>
                <button
                  class="text-xs font-medium text-red-500 hover:text-red-600"
                  type="button"
                  onclick={() => removePasskey(pk.id)}
                  disabled={isBusy}
                >
                  Remove
                </button>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    </div>

    <!-- Data & Migration -->
    <div class="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80 dark:ring-white/10">
      <div class="text-xs uppercase text-slate-500">Data & Migration</div>
      <div class="mt-3">
        <button
          class="flex w-full items-center gap-4 rounded-xl border border-dashed border-slate-200 p-3 text-left transition-all hover:border-slate-300 hover:bg-slate-50/50 dark:border-white/10 dark:hover:bg-white/5"
          onclick={() => currentView.set({ type: 'importer' })}
          type="button"
        >
          <div class="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400">
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
          </div>
          <div class="flex-1">
            <div class="font-medium text-slate-900 dark:text-slate-100">Import from TwoS</div>
            <div class="text-xs text-slate-500 dark:text-slate-400">Bring your lists and things into snipsel</div>
          </div>
          <svg class="h-5 w-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>

    <div class="py-4 text-center text-xs text-slate-400">
      More settings coming soon.
    </div>
  </div>
</div>

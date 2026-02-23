<script lang="ts">
  import { api, type Collection } from '../lib/api';
  import { currentUser } from '../lib/session';
  import { currentView } from '../lib/stores';

  const DEFAULT_HEADER_COLOR = '#4f46e5';

  let defaultHeaderColor = $state('');

  let templateCollections = $state<Collection[]>([]);
  let dayTemplateId = $state<string>('');

  async function logout() {
    await api.logout();
    currentUser.set(null);
    currentView.set({ type: 'loading' });
  }

  async function saveDefaultHeaderColor() {
    const v = defaultHeaderColor.trim() || null;
    const res = await api.updateMe({ default_collection_header_color: v });
    currentUser.set(res.user);
  }

  async function toggleCarryOver() {
    const next = !Boolean($currentUser?.carry_over_open_tasks ?? true);
    const res = await api.updateMe({ carry_over_open_tasks: next });
    currentUser.set(res.user);
  }

  async function loadTemplates() {
    const res = await api.collections.list();
    templateCollections = res.collections.filter((c) => Boolean(c.is_template));
  }

  async function saveDayTemplate() {
    const id = dayTemplateId.trim() || null;
    const res = await api.updateMe({ day_collection_template_id: id });
    currentUser.set(res.user);
  }

  $effect(() => {
    defaultHeaderColor = $currentUser?.default_collection_header_color ?? DEFAULT_HEADER_COLOR;
    dayTemplateId = $currentUser?.day_collection_template_id ?? '';
  });

  $effect(() => {
    loadTemplates();
  });
</script>

<div class="space-y-4">
  <h2 class="flex items-center gap-2 text-2xl font-semibold">
    <svg class="h-6 w-6 text-slate-700" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <path d="M12 15.5a3.5 3.5 0 100-7 3.5 3.5 0 000 7z" />
      <path d="M19.4 15a1.8 1.8 0 00.36 1.98l.05.05a2.2 2.2 0 01-1.56 3.76h-.07a1.8 1.8 0 00-1.98.36 1.8 1.8 0 00-.52 1.27V22a2.2 2.2 0 01-4.4 0v-.07a1.8 1.8 0 00-.36-1.98 1.8 1.8 0 00-1.27-.52H8a2.2 2.2 0 010-4.4h.07a1.8 1.8 0 001.98-.36 1.8 1.8 0 00.52-1.27V12a2.2 2.2 0 014.4 0v.07a1.8 1.8 0 00.36 1.98 1.8 1.8 0 001.27.52H16a2.2 2.2 0 013.4.93z" />
    </svg>
    <span>Settings</span>
  </h2>

  <div class="rounded-lg border bg-white p-5 text-base">
    <div class="text-sm uppercase text-slate-500">Account</div>
    <div class="mt-2 text-lg font-medium">{$currentUser?.username}</div>
    <div class="text-slate-600">{$currentUser?.email}</div>
    <button class="mt-4 rounded-md bg-slate-900 px-4 py-3 text-lg font-medium text-white" type="button" onclick={logout}>
      Logout
    </button>
  </div>

  <div class="rounded-lg border bg-white p-5 text-base">
    <div class="text-sm uppercase text-slate-500">Day template</div>
    <div class="mt-3 space-y-3">
      <select class="w-full rounded-md border px-4 py-3 text-lg" bind:value={dayTemplateId}>
        <option value="">No template</option>
        {#each templateCollections as c (c.id)}
          <option value={c.id}>
            {c.icon} {c.title}
          </option>
        {/each}
      </select>
      <div class="flex gap-2">
        <button class="rounded-md bg-slate-900 px-4 py-3 text-lg font-medium text-white" type="button" onclick={saveDayTemplate}>
          Save
        </button>
        <button
          class="rounded-md border px-4 py-3 text-lg"
          type="button"
          onclick={() => {
            dayTemplateId = '';
            saveDayTemplate();
          }}
        >
          Clear
        </button>
      </div>
    </div>
  </div>

  <div class="rounded-lg border bg-white p-5 text-base">
    <div class="text-sm uppercase text-slate-500">Appearance</div>
    <div class="mt-3">
      <div class="mb-2 text-base font-medium">Default collection header color</div>
      <div class="flex items-center gap-3">
        <input class="h-12 w-16 rounded-md border" type="color" bind:value={defaultHeaderColor} />
        <input class="flex-1 rounded-md border px-4 py-3 text-lg" bind:value={defaultHeaderColor} />
        <button
          class="rounded-md bg-slate-900 px-4 py-3 text-lg font-medium text-white"
          type="button"
          onclick={saveDefaultHeaderColor}
        >
          Save
        </button>
      </div>
    </div>
  </div>

  <div class="rounded-lg border bg-white p-5 text-base">
    <div class="text-sm uppercase text-slate-500">Tasks</div>
    <div class="mt-3 flex items-center justify-between gap-4">
      <div>
        <div class="text-base font-medium">Carry over open tasks</div>
        <div class="text-sm text-slate-500">Move unfinished tasks from the last 30 day lists into today.</div>
      </div>
      <button
        class="rounded-md border px-4 py-3 text-lg"
        type="button"
        onclick={toggleCarryOver}
      >
        {Boolean($currentUser?.carry_over_open_tasks ?? true) ? 'On' : 'Off'}
      </button>
    </div>
  </div>

  <div class="rounded-lg border bg-white p-5 text-base text-slate-600">
    More settings coming soon.
  </div>
</div>

<script lang="ts">
  import { onMount } from 'svelte';
  import { api, type CollectionItem } from '../lib/api';
  import PublicCollectionOutliner from '../lib/PublicCollectionOutliner.svelte';

  let { token } = $props<{ token: string }>();

  let collection = $state<any>(null);
  let items = $state<CollectionItem[]>([]);
  let canWrite = $state(false);
  let loading = $state(true);
  let error = $state<string | null>(null);
  let passcode = $state('');
  let verifyingPasscode = $state(false);
  let passcodeError = $state<string | null>(null);

  async function loadData() {
    loading = true;
    error = null;
    try {
      const res = await api.public.getCollection(token);
      collection = res.collection;
      
      if (collection.is_unlocked) {
        await loadItems();
      }
    } catch (err: any) {
      error = err.error?.message || 'Kollektion konnte nicht geladen werden.';
    } finally {
      loading = false;
    }
  }

  async function loadItems() {
    try {
      const res = await api.public.listSnipsels(token);
      items = res.items;
      canWrite = res.can_write;
    } catch (err: any) {
      error = err.error?.message || 'Inhalt konnte nicht geladen werden.';
    }
  }

  async function handleVerifyPasscode() {
    verifyingPasscode = true;
    passcodeError = null;
    try {
      await api.public.verifyPasscode(token, passcode);
      await loadData(); // Reload to get items
    } catch (err: any) {
      passcodeError = err.error?.message || 'Ungültiger Passcode.';
    } finally {
      verifyingPasscode = false;
    }
  }

  onMount(loadData);
</script>

<div class="public-view" class:is-dark={false}>
  {#if loading}
    <div class="status-center">
      <div class="spinner"></div>
      <p>Lade öffentliche Kollektion...</p>
    </div>
  {:else if error}
    <div class="status-center error">
      <h1>Oops!</h1>
      <p>{error}</p>
    </div>
  {:else if collection && collection.is_passcode_protected && !collection.is_unlocked}
    <div class="status-center passcode-prompt">
      <div class="icon">{collection.icon}</div>
      <h1>{collection.title}</h1>
      <p>Diese Kollektion ist passwortgeschützt.</p>
      
      <div class="input-group">
        <input 
          type="password" 
          placeholder="Passcode eingeben" 
          bind:value={passcode}
          onkeydown={(e) => e.key === 'Enter' && handleVerifyPasscode()}
        />
        <button onclick={handleVerifyPasscode} disabled={verifyingPasscode || !passcode}>
          {verifyingPasscode ? 'Prüfe...' : 'Entsperren'}
        </button>
      </div>
      {#if passcodeError}
        <p class="error-msg">{passcodeError}</p>
      {/if}
    </div>
  {:else if collection}
    <PublicCollectionOutliner 
      {token} 
      {collection} 
      {items} 
      {canWrite}
      onReload={loadItems}
    />
  {/if}
</div>

<style>
  .public-view {
    min-height: 100vh;
    background: #fff;
    color: #333;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  }

  .status-center {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    padding: 2rem;
    text-align: center;
  }

  .spinner {
    width: 40px;
    height: 40px;
    border: 4px solid #f3f3f3;
    border-top: 4px solid #3b82f6;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 1rem;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  .error h1 { color: #ef4444; }
  
  .passcode-prompt .icon { font-size: 4rem; margin-bottom: 1rem; }
  .passcode-prompt h1 { margin-bottom: 0.5rem; }
  
  .input-group {
    display: flex;
    gap: 0.5rem;
    margin-top: 2rem;
    max-width: 400px;
    width: 100%;
  }

  input {
    flex: 1;
    padding: 0.8rem 1rem;
    border: 1px solid #ddd;
    border-radius: 8px;
    font-size: 1rem;
  }

  button {
    padding: 0.8rem 1.5rem;
    background: #3b82f6;
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
  }

  button:disabled { background: #93c5fd; cursor: not-allowed; }

  .error-msg { color: #ef4444; margin-top: 1rem; font-size: 0.9rem; }
</style>

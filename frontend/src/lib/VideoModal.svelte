<script lang="ts">
  import { api } from './api';

  interface Props {
    attachmentId: string | null;
    filename: string;
    onClose: () => void;
  }

  let { attachmentId, filename, onClose }: Props = $props();

  let videoUrl = $state<string | null>(null);
  let loading = $state(false);
  let error = $state<string | null>(null);

  async function loadVideo(id: string) {
    loading = true;
    error = null;
    try {
      const res = await fetch(api.attachments.downloadUrl(id), { credentials: 'include' });
      if (!res.ok) {
        throw new Error('Failed to load video');
      }
      const blob = await res.blob();
      if (videoUrl) {
        URL.revokeObjectURL(videoUrl);
      }
      videoUrl = URL.createObjectURL(blob);
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to load video';
    } finally {
      loading = false;
    }
  }

  function handleBackdropClick(e: MouseEvent) {
    if (e.target === e.currentTarget) {
      onClose();
    }
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') {
      onClose();
    }
  }

  $effect(() => {
    if (attachmentId) {
      loadVideo(attachmentId);
    }
    return () => {
      if (videoUrl) {
        URL.revokeObjectURL(videoUrl);
      }
    };
  });
</script>

<svelte:window onkeydown={handleKeydown} />

{#if attachmentId}
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/90 p-4 backdrop-blur-sm"
    role="dialog"
    aria-modal="true"
    aria-label="Video preview"
    tabindex="-1"
    onclick={handleBackdropClick}
  >
    <div class="relative w-full max-w-4xl max-h-full flex flex-col items-center">
      {#if loading}
        <div class="flex h-64 w-full items-center justify-center rounded-xl bg-slate-900/50">
          <div class="flex flex-col items-center gap-3">
             <div class="h-8 w-8 animate-spin rounded-full border-4 border-slate-600 border-t-indigo-500"></div>
             <div class="text-sm text-slate-400 font-medium">Loading video...</div>
          </div>
        </div>
      {:else if error}
        <div class="flex h-64 w-full items-center justify-center rounded-xl bg-slate-900/50 border border-red-500/20">
          <div class="text-sm text-red-400 font-medium">{error}</div>
        </div>
      {:else if videoUrl}
        <div class="relative w-full overflow-hidden rounded-xl bg-black shadow-2xl ring-1 ring-white/10">
          <video
            src={videoUrl}
            class="w-full h-auto max-h-[80vh]"
            controls
            autoplay
          >
            <track kind="captions" />
            Your browser does not support the video tag.
          </video>
        </div>
      {/if}

      <div class="mt-4 flex items-center justify-center gap-3 w-full">
        <span class="truncate text-sm font-medium text-slate-300 max-w-[200px]">{filename}</span>
        
        {#if videoUrl}
          <a
            class="flex h-9 items-center gap-2 rounded-full bg-white/10 px-4 text-sm font-medium text-white transition-colors hover:bg-white/20"
            href={videoUrl}
            download={filename}
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Download
          </a>
        {/if}
      </div>

      <button
        class="absolute -right-2 -top-12 flex h-10 w-10 items-center justify-center rounded-full bg-white/10 text-white transition-colors hover:bg-white/20 focus:outline-none focus:ring-2 focus:ring-white/20"
        type="button"
        aria-label="Close"
        onclick={onClose}
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  </div>
{/if}

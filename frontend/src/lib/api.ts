export type ApiError = {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
};

export type User = {
  id: string;
  username: string;
  email: string;
  created_at: string;
  default_collection_header_color?: string | null;
  carry_over_open_tasks?: boolean;
};

export type Collection = {
  id: string;
  title: string;
  icon: string;
  header_image_url: string | null;
  header_color?: string | null;
  is_favorite?: boolean;
  default_snipsel_type?: string | null;
  archived: boolean;
  list_for_day: string | null;
  created_at: string;
  modified_at: string;
};

export type Snipsel = {
  id: string;
  type: string;
  content_markdown: string | null;
  task_done: boolean;
  done_at: string | null;
  done_by_id: string | null;
  done_by_username?: string | null;
  external_url: string | null;
  external_label: string | null;
  internal_target_snipsel_id: string | null;
  geo_lat?: number | null;
  geo_lng?: number | null;
  geo_accuracy_m?: number | null;
  created_at: string;
  created_by_id?: string;
  created_by_username?: string | null;
  modified_at: string;
  modified_by_id?: string;
  modified_by_username?: string | null;
  attachments: Array<{
    id: string;
    filename: string;
    mime_type: string | null;
    size_bytes: number;
    has_thumbnail: boolean;
  }>;
};

export type Attachment = {
  id: string;
  filename: string;
  mime_type: string | null;
  size_bytes: number;
  has_thumbnail: boolean;
};

export type CollectionItem = {
  collection_id: string;
  snipsel_id: string;
  position: number;
  indent: number;
  snipsel: Snipsel;
};

export type SearchSnipselHit = {
  id: string;
  type: string;
  content_markdown: string | null;
  task_done: boolean;
  done_at: string | null;
  external_url: string | null;
  external_label: string | null;
  internal_target_snipsel_id: string | null;
  created_at: string;
  modified_at: string;
};

export type SearchCollectionHit = {
  id: string;
  title: string;
  icon: string;
  list_for_day: string | null;
};

export type SearchResponse = {
  snipsels: SearchSnipselHit[];
  collections: SearchCollectionHit[];
};

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  const data = (await res.json()) as T | ApiError;
  if (!res.ok) {
    throw data;
  }
  return data as T;
}

export const api = {
  register: (input: { username: string; email: string; password: string }) =>
    requestJson<{ user: User }>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(input),
    }),
  login: (input: { username: string; password: string }) =>
    requestJson<{ user: User }>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify(input),
    }),
  logout: () => requestJson<{ ok: true }>('/api/auth/logout', { method: 'POST' }),
  me: () => requestJson<{ user: User }>('/api/auth/me'),
  updateMe: (input: { default_collection_header_color?: string | null; carry_over_open_tasks?: boolean }) =>
    requestJson<{ user: User }>('/api/auth/me', {
      method: 'PATCH',
      body: JSON.stringify(input),
    }),

  collections: {
    list: (includeArchived = false) =>
      requestJson<{ collections: Collection[] }>(
        `/api/collections${includeArchived ? '?include_archived=1' : ''}`
      ),
    get: (id: string) =>
      requestJson<{ collection: Collection }>(`/api/collections/${id}`),
    today: (day?: string) =>
      requestJson<{ collection: Collection }>(
        `/api/collections/today${day ? `?day=${day}` : ''}`
      ),
    create: (input: {
      title: string;
      icon?: string;
      header_image_url?: string;
      header_color?: string;
      is_favorite?: boolean;
      default_snipsel_type?: string;
    }) =>
      requestJson<{ collection: Collection }>('/api/collections', {
        method: 'POST',
        body: JSON.stringify(input),
      }),
    update: (
      id: string,
      input: {
        title?: string;
        icon?: string;
        header_image_url?: string;
        header_color?: string;
        archived?: boolean;
        is_favorite?: boolean;
        default_snipsel_type?: string;
      }
    ) =>
      requestJson<{ collection: Collection }>(`/api/collections/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(input),
      }),
    delete: (id: string) =>
      requestJson<{ ok: true }>(`/api/collections/${id}`, { method: 'DELETE' }),
  },

  snipsels: {
    list: (collectionId: string) =>
      requestJson<{ items: CollectionItem[] }>(
        `/api/collections/${collectionId}/snipsels`
      ),
    get: (snipselId: string) =>
      requestJson<{ snipsel: Snipsel }>(`/api/snipsels/${snipselId}`),
    create: (
      collectionId: string,
      input: {
        type?: string;
        content_markdown?: string;
        geo_lat?: number;
        geo_lng?: number;
        geo_accuracy_m?: number;
      }
    ) =>
      requestJson<{ item: CollectionItem }>(
        `/api/collections/${collectionId}/snipsels`,
        {
          method: 'POST',
          body: JSON.stringify(input),
        }
      ),
    update: (
      snipselId: string,
      input: {
        type?: string;
        content_markdown?: string | null;
        task_done?: boolean;
        external_url?: string;
        external_label?: string;
        internal_target_snipsel_id?: string;
      }
    ) =>
      requestJson<{ snipsel: Snipsel }>(`/api/snipsels/${snipselId}`, {
        method: 'PATCH',
        body: JSON.stringify(input),
      }),
    delete: (collectionId: string, snipselId: string) =>
      requestJson<{ ok: true }>(
        `/api/collections/${collectionId}/snipsels/${snipselId}`,
        { method: 'DELETE' }
      ),
    copy: (collectionId: string, snipselId: string) =>
      requestJson<{ item: CollectionItem }>(
        `/api/collections/${collectionId}/snipsels/${snipselId}/copy`,
        { method: 'POST' }
      ),
    reference: (collectionId: string, snipselId: string) =>
      requestJson<{ item: CollectionItem }>(
        `/api/collections/${collectionId}/snipsels/${snipselId}/reference`,
        { method: 'POST' }
      ),
    reorder: (
      collectionId: string,
      items: Array<{ snipsel_id: string; position: number; indent: number }>
    ) =>
      requestJson<{ ok: true }>(
        `/api/collections/${collectionId}/snipsels/reorder`,
        {
          method: 'PATCH',
          body: JSON.stringify({ items }),
        }
      ),
  },

  attachments: {
    upload: async (snipselId: string, file: File) => {
      const form = new FormData();
      form.append('file', file);
      const res = await fetch(`/api/snipsels/${snipselId}/attachments`, {
        method: 'POST',
        credentials: 'include',
        body: form,
      });
      const data = (await res.json()) as { attachment: Attachment } | ApiError;
      if (!res.ok) throw data;
      return data as { attachment: Attachment };
    },
    delete: async (attachmentId: string) => {
      const res = await fetch(`/api/attachments/${attachmentId}`, {
        method: 'DELETE',
        credentials: 'include',
      });
      const data = (await res.json()) as { ok: true } | ApiError;
      if (!res.ok) throw data;
      return data as { ok: true };
    },
    downloadUrl: (attachmentId: string) => `/api/attachments/${attachmentId}`,
    thumbnailUrl: (attachmentId: string) => `/api/attachments/${attachmentId}/thumbnail`,
  },

  search: (params: {
    q?: string;
    tag?: string;
    mention?: string;
    type?: string;
    include_archived?: boolean;
    day?: string;
  }) => {
    const sp = new URLSearchParams();
    if (params.q) sp.set('q', params.q);
    if (params.tag) sp.set('tag', params.tag);
    if (params.mention) sp.set('mention', params.mention);
    if (params.type) sp.set('type', params.type);
    if (params.include_archived) sp.set('include_archived', '1');
    if (params.day) sp.set('day', params.day);
    const qs = sp.toString();
    return requestJson<SearchResponse>(`/api/search${qs ? `?${qs}` : ''}`);
  },
};

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
  day_collection_template_id?: string | null;
};

export type Collection = {
  id: string;
  title: string;
  icon: string;
  header_image_url: string | null;
  header_color?: string | null;
  is_favorite?: boolean;
  is_template?: boolean;
  default_snipsel_type?: string | null;
  archived: boolean;
  list_for_day: string | null;
  created_at: string;
  modified_at: string;
  access_level?: 'owner' | 'write' | 'read';
  shared_by_username?: string | null;
  shared_out?: boolean;
  modified_by_id?: string;
  modified_by_username?: string | null;
};

export type UserLite = { id: string; username: string };

export type CollectionShare = {
  id: string;
  shared_with_user_id: string;
  shared_with_username?: string | null;
  permission: 'read' | 'write';
  created_at: string;
};

export type Notification = {
  id: string;
  message: string;
  is_read: boolean;
  snipsel_id?: string | null;
  collection_id?: string | null;
  created_at: string;
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
  tags?: string[];
  mentions?: string[];
};

export type SnipselDetailResponse = {
  snipsel: Snipsel;
  tags?: string[];
  mentions?: string[];
  placements?: Array<{ collection_id: string; position: number; indent: number }>;
  backlinks?: Array<{ from_snipsel_id: string; to_snipsel_id: string }>;
  has_collection_access?: boolean;
  has_write_access?: boolean;
  can_toggle_task_done?: boolean;
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
  collection_refs?: Array<{ title: string; collection_id: string }>;
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
  collection_id?: string | null;
  collection_title?: string | null;
  collection_icon?: string | null;
  position?: number | null;
  has_collection_access?: boolean;
  has_write_access?: boolean;
  can_toggle_task_done?: boolean;
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

export type TagCount = { name: string; count: number };

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
  updateMe: (input: {
    default_collection_header_color?: string | null;
    carry_over_open_tasks?: boolean;
    day_collection_template_id?: string | null;
  }) =>
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
        is_template?: boolean;
        default_snipsel_type?: string;
      }
    ) =>
      requestJson<{ collection: Collection }>(`/api/collections/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(input),
      }),

    favorite: (id: string) => requestJson<{ ok: true }>(`/api/collections/${id}/favorite`, { method: 'POST' }),
    unfavorite: (id: string) => requestJson<{ ok: true }>(`/api/collections/${id}/favorite`, { method: 'DELETE' }),
    delete: (id: string) =>
      requestJson<{ ok: true }>(`/api/collections/${id}`, { method: 'DELETE' }),
    autocomplete: (q: string) =>
      requestJson<{ collections: Array<{ id: string; title: string; icon: string }> }>(
        `/api/collections/autocomplete?q=${encodeURIComponent(q)}`
      ),

    listShares: (id: string) =>
      requestJson<{ shares: CollectionShare[] }>(`/api/collections/${id}/shares`),
    createShare: (id: string, input: { shared_with_user_id: string; permission: 'read' | 'write' }) =>
      requestJson<{ share: { id: string } }>(`/api/collections/${id}/shares`, {
        method: 'POST',
        body: JSON.stringify(input),
      }),
    deleteShare: (id: string, shareId: string) =>
      requestJson<{ ok: true }>(`/api/collections/${id}/shares/${shareId}`, { method: 'DELETE' }),

    insertTemplate: (id: string, templateCollectionId: string) =>
      requestJson<{ ok: true }>(`/api/collections/${id}/insert_template`, {
        method: 'POST',
        body: JSON.stringify({ template_collection_id: templateCollectionId }),
      }),
  },

  users: {
    list: () => requestJson<{ users: UserLite[] }>('/api/users'),
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

  notifications: {
    list: () => requestJson<{ notifications: Notification[] }>('/api/notifications'),
    markRead: (id: string) => requestJson<{ success: boolean }>(`/api/notifications/${id}/mark-read`, { method: 'POST' }),
    markAllRead: () => requestJson<{ success: boolean }>('/api/notifications/mark-all-read', { method: 'POST' }),
    deleteRead: () => requestJson<{ success: boolean }>('/api/notifications/read', { method: 'DELETE' }),
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
    mentions_me?: boolean;
    type?: string;
    task_done?: boolean;
    include_archived?: boolean;
    day?: string;
    scope?: 'my' | 'shared' | 'all';
  }) => {
    const sp = new URLSearchParams();
    if (params.q) sp.set('q', params.q);
    if (params.tag) sp.set('tag', params.tag);
    if (params.mention) sp.set('mention', params.mention);
    if (params.mentions_me) sp.set('mentions_me', '1');
    if (params.type) sp.set('type', params.type);
    if (typeof params.task_done === 'boolean') sp.set('task_done', params.task_done ? '1' : '0');
    if (params.include_archived) sp.set('include_archived', '1');
    if (params.day) sp.set('day', params.day);
    if (params.scope) sp.set('scope', params.scope);
    const qs = sp.toString();
    return requestJson<SearchResponse>(`/api/search${qs ? `?${qs}` : ''}`);
  },

  tags: {
    list: (scope?: 'my' | 'shared' | 'all', q?: string) => {
      const sp = new URLSearchParams();
      if (scope) sp.set('scope', scope);
      if (q) sp.set('q', q);
      const qs = sp.toString();
      return requestJson<{ tags: TagCount[] }>(`/api/tags${qs ? `?${qs}` : ''}`);
    },
  },

  mentions: {
    list: (scope?: 'my' | 'shared' | 'all', q?: string) => {
      const sp = new URLSearchParams();
      if (scope) sp.set('scope', scope);
      if (q) sp.set('q', q);
      const qs = sp.toString();
      return requestJson<{ mentions: TagCount[] }>(`/api/mentions${qs ? `?${qs}` : ''}`);
    },
  },
};

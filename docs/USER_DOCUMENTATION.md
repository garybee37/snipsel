# Snipsel - User Documentation

## Purpose

Snipsel is a personal knowledge management application that helps you organize notes, tasks, and ideas in collections. It combines the flexibility of a note-taking app with powerful features like tagging, mentions, and search to help you quickly find and connect your information.

## Key Features (Overview)

- **Collections** - Organize your content into themed collections
- **Daily Collections** - Automatic daily notes for each day
- **Snipsels** - Individual notes within collections (text, tasks, links, images)
- **Tags** - Categorize snipsels with #hashtags
- **Mentions** - Reference other users with @username
- **Search** - Find content across all collections
- **Sharing** - Share collections with other users
- **Passcode Protection** - Secure sensitive collections
- **Notifications** - Stay informed about mentions and task assignments
- **Reminders** - Set date-based alerts for individual snipsels

---

## Collections

### What is a Collection?

A collection is a container for related snipsels. Think of it like a notebook or folder. Each collection has:
- **Title** - Name of the collection
- **Icon** - Emoji icon for visual identification
- **Header Color** - Custom color for the collection header
- **Default Snipsel Type** - Preferred type for new snipsels

### Regular Collections

Regular collections are manual containers you create to organize content thematically. Examples:
- "Project Ideas"
- "Meeting Notes"
- "Reading List"

### Daily Collections

Daily collections are automatically created for each day. They provide a quick way to capture daily thoughts, tasks, and notes without creating a collection manually.

**Key behaviors:**
- One collection per day per user (unique by owner + date)
- Shown in the Calendar view
- When viewing your daily collection, you can see snipsels from other users that mention you (read-only)
- Useful for daily standups, journal entries, or daily task lists

![Screenshot: Daily Collection in Calendar View - PLACEHOLDER]

### Creating a Collection

1. Click the **+** button in the sidebar
2. Enter a title for the collection
3. Optionally select an icon and header color
4. Choose a default snipsel type (optional)
5. Click **Create**

### Collection Settings

Access collection settings by clicking the collection menu (three dots) and selecting **Settings**. Options include:
- Rename collection
- Change icon and color
- Set default snipsel type
- Enable/disable passcode protection
- Archive collection
- Delete collection

---

## Snipsels

### What is a Snipsel?

A snipsel is an individual item within a collection. It's the basic unit of content in Snipsel.

### Snipsel Types

1. **Text** - Plain text or markdown content
2. **Task** - A task that can be marked as done/undone
3. **Link** - External URL with optional label
4. **Image** - Image attachments displayed in a grid
5. **Attachment** - File attachments

### Creating a Snipsel

1. Open a collection
2. Click **Add new snipsel** (or press Enter after the last snipsel)
3. The new snipsel inherits the indent level from the previous snipsel
4. Select the type using the dropdown (text, task, link, image)
5. Enter content and press **Save**

### Editing Snipsel Content

- Click on any snipsel to edit it
- Supports Markdown formatting (Bold, Italic, Lists, **Blockquotes** using `>`, etc.)
- Tags and mentions are automatically extracted and linked

### Task Management

For **task** type snipsels:
- Click the checkbox to mark as done/undone.
- Done tasks show a strikethrough.
- **Recurring Tasks**: When you mark a task with a recurring reminder as done, a new open task is automatically created for the next occurrence and placed directly below the completed one. This ensures you never "lose" a task that hasn't been finished yet.
- Tasks assigned to you via @mention will appear in your notifications.

### Reminders

You can set date-based reminders for any snipsel:
1. Open the snipsel detail (click the "edit" or "expand" icon).
2. Use the **Reminders** card to set a date and time.
3. **Recurrence**: Enter a standard iCalendar RRule (e.g., `FREQ=DAILY`) for repeating reminders.
4. **Behavior**: 
    - Reminders **stay on the task** even if the date passes, as long as the task is open.
    - When a recurring task is **marked as done**, the system automatically creates a **copy** of the task with the next reminder date and places it directly below the completed task.
    - If you complete a task early, the next date is still calculated based on the original series to maintain your schedule.
5. **Icon**: Tasks with recurring reminders show a curved arrow icon next to the date.
6. **Display**: Reminders are shown in the collection view and the dedicated **Tasks** page.

---

## Tasks Page

The **Tasks** page (accessible via the checkmark icon in the sidebar) provides a central view of all your tasks across all collections.

### Filtering Tasks

1. **Open / Done**: Switch between pending and completed tasks.
2. **My / Shared**: 
    - **My**: Shows tasks you created yourself that are NOT explicitly assigned to someone else via `@mention`.
    - **Shared**: Shows tasks created by others in collections shared with you, provided they are NOT explicitly assigned to a specific user.
- **Template Exclusion**: Tasks from collections marked as **Templates** are hidden from the main Todos view to avoid clutter. However, they remain accessible via the global search.

> [!NOTE]
> Tasks that contain an `@username` mention of a known user are considered "assigned" and will not appear in the general **My** or **Shared** lists. They will instead appear in the notifications and mentions of the respective user.

### Sorting

Tasks are sorted by their reminder date (if set), with the soonest or overdue tasks appearing at the top.

### Attachments

**Image Type:**
- Click to upload images
- Images display in a grid layout
- Click any image to view full size
- Thumbnails are auto-generated with correct rotation (EXIF-aware)

**Attachment Type:**
- Upload any file type
- Files show as download links
- Maximum file size: 10MB per file

![Screenshot: Snipsel with image attachments - PLACEHOLDER]

### Indent / Nesting

Snipsels can be indented to create hierarchy:
- Use the indent controls on the snipsel (or keyboard shortcuts)
- Indented snipsels are visually nested
- Helps organize related content

---

## Tags

### Using Tags

Tags are words prefixed with `#` that help categorize snipsels. Examples:
- `#project-alpha`
- `#ideas`
- `#read-later`

### How Tags Work

1. Add `#tagname` anywhere in snipsel content
2. Tags are automatically detected when saving
3. Tags are linked to the snipsel owner
4. You can filter snipsels by tag

### Tag Scope

When searching or filtering tags, you can choose scope:
- **My tags** - Tags you created (#mytag)
- **Shared tags** - Tags from others (#someone-else)
- **All tags** - Everything

### Tag Navigation

- Click any tag to filter snipsels by that tag
- Tags page shows all tags with snipsel counts

![Screenshot: Tag filtering - PLACEHOLDER]

---

## Mentions

### Using Mentions

Mention other users with `@username` to:
- Notify them about relevant content
- Assign tasks to them
- Reference their input

### How Mentions Work

1. Type `@username` in any snipsel
2. When saved, the mentioned user receives a notification
3. For tasks: "User assigned a task to you"
4. For other content: "User mentioned you in a snipsel"

### Viewing Mentions

**In your collection:**
- Mentions you receive appear in notifications

**In Daily Collections:**
- When viewing your daily collection, you see snipsels from other users that mention you
- These are shown in a "Mentioned by others on this day" section
- Read-only view (you can see but not edit)
- Shows the author's username

![Screenshot: Incoming mentions in daily collection - PLACEHOLDER]

### Mention Notifications

Notifications are sent for:
- Being mentioned in any snipsel
- Being assigned a task
- Collection sharing invitations

---

## Search

### Basic Search

Enter search terms in the search bar to find snipsels across all your collections.

### Search Behavior

- **AND Logic**: All search terms must match
- Example: Searching "project meeting" finds snipsels containing BOTH "project" AND "meeting"
- Searches: snipsel content, external URLs, external labels

### Search Filters

You can narrow search results with:
- **Type**: text, task, link, image, attachment
- **Tag**: Filter by specific tag
- **Mention**: Filter by mention (@user)
- **Day**: Filter by date
- **Scope**: my, shared, or all collections
- **Task Done**: Filter completed/incomplete tasks

### Search Results

Results show:
- Snipsel content preview
- Collection it belongs to
- Last modified date
- Write access indicator

---

## Permissions & Sharing

### Permission Levels

1. **Owner** - Full control, can delete collection
2. **Write** - Can add/edit snipsels
3. **Read** - View-only access

### Sharing a Collection

1. Open collection settings
2. Click **Share**
3. Enter the username to share with
4. Select permission (Read or Write)
5. The shared user will see the collection in their sidebar

### Sharing Daily Collections

**Important distinction:**

| Feature | Regular Collections | Daily Collections |
|---------|--------------------|--------------------|
| Manual sharing | Yes - via collection settings | No - cannot share |
| Visibility | Only owner + shared users | Only owner (private) |
| Cross-user mentions | Read-only in mentions section | Yes - view others' snipsels mentioning you |

**Daily Collections:**
- Cannot be shared through settings
- However, when OTHER users mention you in THEIR daily collections, you can see those mentions in YOUR daily collection
- This enables cross-user collaboration on the same day without explicit sharing

### Passcode Protection

Protect sensitive collections with a passcode:
1. Open collection settings
2. Enable **Passcode Protection**
3. Set a passcode
4. Users must enter passcode to view collection content

---

## Notifications

### Notification Types

1. **Mention** - Someone mentioned you in a snipsel
2. **Task Assignment** - You were assigned a task
3. **Share** - A collection was shared with you
4. **Reminder** - A snipsel reminder time has been reached

### Viewing Notifications

- Click the bell icon in the header
- Shows unread count badge
- Click to mark as read
- Click notification to jump to relevant snipsel

---

## Calendar View

The calendar shows your daily collections organized by date.

### Features

- Month view with dots indicating days with collections
- Click any day to view that day's collection
- Navigate between months
- Today's collection highlighted

![Screenshot: Calendar View - PLACEHOLDER]

---

## Security & Authentication

Snipsel provides modern security features to keep your account safe. These can be configured in your **Settings**.

### Two-Factor Authentication (2FA)

You can enable 2FA to add an extra layer of security to your account.
1. Open Settings and click **Enable 2FA**.
2. Scan the QR code with your authenticator app (e.g., Google Authenticator, Authy, Apple Passwords).
3. Enter the 6-digit code and your current password to verify and enable.
4. On future logins, you will be prompted to enter a 6-digit code after your password.

### Passkeys

Passkeys allow you to log in securely without a password using your device's built-in authentication (Touch ID, Face ID, Windows Hello) or a hardware security key.

**Adding a Passkey:**
1. Open Settings and look for the **Login with Passkey** section.
2. Enter a name for your device (e.g., "MacBook Pro" or "iPhone").
3. Click **Add Passkey** and follow your browser/device prompts.

**Logging in with a Passkey:**
1. On the login screen, click the **Login with Passkey** button.
2. If you only have one passkey or have used one recently, your device will prompt you to authenticate. Alternatively, you can type your username first, and then click the button.

---

## Settings

### Personal Settings

Access via the settings icon (gear):
- Change username
- View account info

### Collection Settings

Per-collection settings (accessed via collection menu):
- Title, icon, color
- Default snipsel type
- Passcode protection
- Sharing management
- Archive/Delete

---

## Keyboard Shortcuts

- **Enter** after last snipsel: Create new snipsel
- **Tab**: Increase indent
- **Shift+Tab**: Decrease indent
- **Ctrl+Enter**: Save snipsel (when editing)

---

### Maintenance

#### Cleanup Command

To permanently delete all snipsels and collections marked as "deleted" (including physical attachment files and their thumbnails), run the following command from the `backend` directory:

```bash
flask --app snipsel_api.app cleanup
```

This command:
1. Identifies all items with a `deleted_at` timestamp.
2. Removes associated physical files from the storage directory.
3. Completely removes the database records and all their relationships (tags, mentions, shares, etc.).

---

## Technical Notes

### Image Handling
... (unchanged)

### Image Handling

- Thumbnails are auto-generated for images
- EXIF rotation metadata is respected (photos from phones display correctly)
- Supported formats: JPEG, PNG, GIF, WebP

### Data Storage

- All data stored in SQLite database
- File uploads stored in `./uploads/` directory
- Automatic thumbnail generation

### Security

- Sessions managed via secure cookies
- Passwords hashed with bcrypt
- Passcode collections require code to access

### Docker Deployment

To deploy Snipsel using Docker (frontend and backend in one container):

```bash
# 1. Build the Docker image
docker build -t snipsel .

# 2. Run the container
docker run -d \
  --name snipsel \
  -p 5000:5000 \
  -v ./snipsel_data:/app/data \
  -v ./snipsel_uploads:/app/uploads \
  -e SNIPSEL_SECRET_KEY="your-secure-secret-key" \
  -e SNIPSEL_DOMAIN="yourdomain.com" \
  -e SNIPSEL_FRONTEND_URL="https://yourdomain.com" \
  -e VAPID_PUBLIC_KEY="your_vapid_public_key" \
  -e VAPID_PRIVATE_KEY="your_vapid_private_key" \
  -e VAPID_SUBJECT="mailto:admin@yourdomain.com" \
  snipsel
```

**Required Environment Variables for Passkeys:**
If you want to use Passkeys, you *must* set `SNIPSEL_DOMAIN` and `SNIPSEL_FRONTEND_URL` to match your production domain. Without them, WebAuthn will fail.
For Push Notifications, you must set `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, and `VAPID_SUBJECT`.

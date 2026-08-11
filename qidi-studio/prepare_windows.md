# QIDI Studio Windows Setup

This guide explains how to link your local QIDI Studio configuration to this Git repository using the `prepare_windows.cmd` script.

## What This Does
QIDI Studio stores its user profiles in `%AppData%\QIDIStudio\user`. In modern versions (v2.7+), logging in with a QIDI account creates a numeric ID directory (e.g., `user\2032448788926902273`) alongside the default local folder (`user\default`).

The `prepare_windows.cmd` script will automatically:
1. Scan your `%AppData%\QIDIStudio\user` folder to find all active account directories (both `default` and any numeric ID profiles).
2. For each account folder, it checks if `process`, `filament`, and `machine` directories already exist.
3. If they exist as regular folders, it safely renames them with a `_backup` suffix (e.g., `process_backup`) so you don't lose any configuration.
4. It creates Windows Symbolic Links inside each account folder pointing directly to this Git repository's folders.

## Step 1: Run the Script
1. Before running, open `prepare_windows.cmd` in an editor and ensure the `gitDir` variable matches the exact path to this repository on your machine.
2. Open Windows Explorer and navigate to this repository.
3. Right-click **`prepare_windows.cmd`** and select **Run as Administrator** (Admin rights are required by Windows to create symbolic links).
4. Wait for the script to say "Setup Complete!".

## Step 2: Restore Your Backups
Because the script safely moves your existing files out of the way instead of overwriting them, you must manually move your existing profiles into the newly linked Git folders.

1. Press `Win + R`, paste the following path, and hit Enter:
   ```text
   %AppData%\QIDIStudio\user
   ```
2. Navigate to your active account folder (either `default` or your numeric ID folder).
3. You will see your new linked folders (indicated by shortcut icons) next to your backup folders (e.g., `process_backup`).
4. Open the `_backup` folders, copy all the `.json` and `.info` files inside, and paste them directly into the newly linked folders.
5. Once your files are moved and safe, you can delete the `_backup` folders to clean up your AppData directory.

## Step 3: Verify and Commit
1. Open QIDI Studio and verify your custom profiles appear in the dropdown menus.
2. In VSCode (or your terminal), check your Git status. You should now see all your `.json` profiles staged as untracked files in this repository.
3. Commit and push your setup!

```bash
git add .
git commit -m "Migrated QIDI Studio profiles to Git via symbolic links"
git push
```
# QIDI Studio Windows Setup

This guide explains how to link your local QIDI Studio configuration to this Git repository using the `prepare_windows.cmd` script.

## What This Does
QIDI Studio stores its user profiles in `%AppData%\QIDIStudio\user\default`. To allow version control and AI agent access without constantly copying files manually, we use **Symbolic Links**. 

The `prepare_windows.cmd` script will:
1. Check your Windows AppData folder for existing QIDI profiles.
2. Safely rename any existing folders (`process`, `filament`, `machine`) to have a `_backup` suffix.
3. Create a symbolic link from AppData pointing directly to this Git repository.

## Step 1: Run the Script
1. Before running, open `prepare_windows.cmd` in an editor and ensure the `gitDir` variable matches the exact path to this repository on your machine.
2. Open Windows Explorer and navigate to this repository.
3. Right-click **`prepare_windows.cmd`** and select **Run as Administrator**.
   *(Note: Administrator privileges are required to create Symbolic Links in Windows).*
4. Wait for the script to say "Setup Complete!".

## Step 2: Restore Your Backups
Because the script safely moves your existing files out of the way instead of overwriting them, you must manually move your existing profiles into the newly linked Git folders.

1. Press `Win + R`, paste the following path, and hit Enter:
   ```text
   %AppData%\QIDIStudio\user\default
   ```
2. You will see your new linked folders (with shortcut arrows) alongside your old backup folders (e.g., `process_backup`).
3. Open `process_backup`, copy all the `.json` files inside, and paste them directly into the newly linked `process` folder.
4. Repeat this process for `filament_backup` and `machine_backup`.
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
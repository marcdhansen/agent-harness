#!/usr/bin/env python3
"""
Git worktree management with cleanup validation (agent-6x9.4)

Uses subprocess for git commands (consistent with existing codebase)
"""

import subprocess
import time
import uuid
from pathlib import Path


class WorktreeCleanupError(Exception):
    """Raised when worktree cleanup validation fails"""

    pass


class GitWorktreeManager:
    """Manage git worktrees with cleanup enforcement"""

    def __init__(self, repo_path: Path = None):
        self.repo_path = repo_path or Path.cwd()
        self._active_worktrees = {}

    def create_worktree(self, agent_id: str, base_branch: str = "main") -> Path:
        """Create isolated worktree for agent"""
        branch_name = f"agent/{agent_id}/{uuid.uuid4().hex[:8]}"
        worktree_path = self.repo_path.parent / f"worktree-{agent_id}"

        # Create worktree using subprocess (consistent with codebase)
        subprocess.run(
            ["git", "worktree", "add", str(worktree_path), "-b", branch_name, base_branch],
            check=True,
            cwd=self.repo_path,
        )

        # Track worktree
        self._active_worktrees[agent_id] = {
            "path": worktree_path,
            "branch": branch_name,
            "created_at": time.time(),
        }

        return worktree_path

    def remove_worktree(
        self, agent_id: str, keep_branch: bool = False, validate_cleanup: bool = True
    ) -> None:
        """Remove worktree with optional cleanup validation"""
        if agent_id not in self._active_worktrees:
            return

        worktree = self._active_worktrees[agent_id]

        # Validate cleanup if requested
        if validate_cleanup:
            violations = self.validate_worktree_cleanup(worktree["path"])
            if violations:
                raise WorktreeCleanupError(
                    f"Worktree cleanup incomplete for {agent_id}:\n"
                    + "\n".join(f"  - {v}" for v in violations)
                )

        # Remove worktree
        subprocess.run(
            ["git", "worktree", "remove", str(worktree["path"]), "--force"],
            check=True,
            cwd=self.repo_path,
        )

        # Delete branch if requested
        if not keep_branch:
            subprocess.run(
                ["git", "branch", "-D", worktree["branch"]], check=True, cwd=self.repo_path
            )

        # Remove from tracking
        del self._active_worktrees[agent_id]

    def validate_worktree_cleanup(self, worktree_path: Path) -> list[str]:
        """
        Validate worktree is clean before removal

        Checks:
        1. No temporary files (matches cleanup_patterns.txt)
        2. No uncommitted changes
        3. No large files (>10MB)

        Returns list of violations (empty if clean)
        """
        if not worktree_path.exists():
            return []

        violations = []

        # Check 1: Temporary files using existing patterns
        temp_patterns = [
            "*.tmp",
            "*.temp",
            "*_scratch.*",
            "debug_*",
            "test_temp_*",
            "WIP_*",
            "*.notes",
        ]

        for pattern in temp_patterns:
            files = list(worktree_path.rglob(pattern))
            # Filter out .git and other excluded dirs
            files = [f for f in files if not any(part.startswith(".git") for part in f.parts)]
            if files:
                violations.append(
                    f"Temporary files ({pattern}): " + f"{[f.name for f in files[:3]]}"
                )

        # Check 2: Uncommitted changes
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=worktree_path,
                capture_output=True,
                text=True,
                check=True,
            )

            if result.stdout.strip():
                violations.append("Uncommitted changes in worktree")
        except subprocess.CalledProcessError:
            violations.append("Could not check git status")

        # Check 3: Large files (>10MB)
        large_files = []
        for file in worktree_path.rglob("*"):
            if file.is_file() and file.stat().st_size > 10_000_000:
                large_files.append(file.name)

        if large_files:
            violations.append(f"Large files (>10MB): {large_files[:3]}")

        return violations

    def list_worktrees(self) -> list[dict]:
        """List all active worktrees using subprocess"""
        try:
            result = subprocess.run(
                ["git", "worktree", "list", "--porcelain"],
                capture_output=True,
                text=True,
                check=True,
                cwd=self.repo_path,
            )
        except subprocess.CalledProcessError:
            return []

        worktrees = []
        current = {}

        for line in result.stdout.splitlines():
            if line.startswith("worktree "):
                if current:
                    worktrees.append(current)
                current = {"path": line.split(" ", 1)[1]}
            elif line.startswith("branch "):
                current["branch"] = line.split(" ", 1)[1]
            elif line.startswith("HEAD "):
                current["head"] = line.split(" ", 1)[1]

        if current:
            worktrees.append(current)

        return worktrees

    def cleanup_orphaned_worktrees(self) -> list[str]:
        """
        Find and clean up orphaned worktrees

        Returns list of cleaned worktree paths
        """
        # Prune references to removed worktrees
        subprocess.run(["git", "worktree", "prune"], check=True, cwd=self.repo_path)

        cleaned = []
        worktrees = self.list_worktrees()

        for wt in worktrees:
            path = Path(wt["path"])

            # Skip main worktree
            if path == self.repo_path:
                continue

            # Check if orphaned (path doesn't exist)
            if not path.exists():
                cleaned.append(str(path))
                continue

            # Check age (older than 24 hours with no recent activity)
            try:
                mtime = path.stat().st_mtime
                age_hours = (time.time() - mtime) / 3600

                if age_hours > 24:
                    # Check if it's truly abandoned
                    result = subprocess.run(
                        ["git", "status", "--porcelain"], cwd=path, capture_output=True, text=True
                    )

                    if result.returncode == 0 and not result.stdout.strip():
                        # Clean worktree with no changes - remove it
                        try:
                            subprocess.run(
                                ["git", "worktree", "remove", str(path), "--force"],
                                check=True,
                                cwd=self.repo_path,
                            )
                            cleaned.append(str(path))
                        except Exception:
                            pass
            except Exception:  # nosec
                continue

        return cleaned

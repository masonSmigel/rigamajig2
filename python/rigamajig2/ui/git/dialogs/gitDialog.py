#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: git_dialog.py
    author: masonsmigel
    date: 09/2023
    description:

"""
import logging
import os

from PySide2 import QtCore
from PySide2 import QtWidgets

from rigamajig2.ui.resources import Resources
from rigamajig2.ui.widgets import mayaDialog, mayaMessageBox

logger = logging.getLogger(__name__)

try:
    import git

    _gitLoaded = True
except ModuleNotFoundError:
    logger.error("python module 'git' not found. Git features are not available. (please install requirements.txt)")
    _gitLoaded = False


ITEM_HEIGHT = 18


def isRepoInitialized(repo_path):
    try:
        # Attempt to open an existing Repo object with the given path
        repo = git.Repo(repo_path)
        return True  # Repo is initialized
    except git.exc.InvalidGitRepositoryError:
        return False  # Repo does not exist or is not initialized


def intializeRepo(repo_path):
    repo = git.Repo.init(repo_path)

    # add the .DS_Store to the .gitignore
    gitignore_path = os.path.join(repo.working_tree_dir, ".gitignore")

    addToGitIgnore(repo_path, items_to_ignore=["*.DS_Store"])

    # Commit the changes to the repository
    repo.index.add([gitignore_path])
    repo.index.commit(f"Repo intialized")


def addToGitIgnore(repo_path, items_to_ignore):
    repo = git.Repo(repo_path)
    gitignore_path = os.path.join(repo.working_tree_dir, ".gitignore")

    # Check if .gitignore exists; create it if it doesn't
    if not os.path.exists(gitignore_path):
        with open(gitignore_path, "w") as gitignore_file:
            gitignore_file.write("# .gitignore file\n")

    # Read existing entries from .gitignore
    with open(gitignore_path, "r") as gitignore_file:
        existing_entries = gitignore_file.read().splitlines()

    # Add new items to .gitignore if they don't already exist
    with open(gitignore_path, "a") as gitignore_file:
        for item in items_to_ignore:
            if item not in existing_entries:
                gitignore_file.write(f"{item}\n")
                existing_entries.append(item)


class GitDialog(mayaDialog.MayaDialog):
    WINDOW_TITLE = "Git Version History"
    WINDOW_SIZE = (200, 450)

    def __init__(self, repoPath=None):
        super().__init__()

        self.repo = None
        # Initialize gitPython repo using the specified path
        if repoPath:
            self.setRepo(repoPath)
            self.loadFilesChangedSinceLastCommit()
            self.loadCommitHistory()
            self.updateWatcherFiles(self.repo)

    def createWidgets(self):
        # Label to display the current repo
        self.repoLabel = QtWidgets.QLineEdit()
        self.repoLabel.setDisabled(True)

        self.refreshAllButton = QtWidgets.QPushButton()
        self.refreshAllButton.setIcon(Resources.getIcon(":refresh.png"))
        self.refreshAllButton.setMaximumSize(20, 20)
        self.refreshAllButton.setFlat(True)

        # Files Changed Since Last Commit section
        self.filesChangedList = QtWidgets.QListWidget()
        self.filesChangedList.setAlternatingRowColors(True)
        self.filesChangedList.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.filesChangedList.setUniformItemSizes(True)
        self.filesChangedList.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.filesChangedList.customContextMenuRequested.connect(self.showFileChangelistContextMenu)

        # Commit section
        self.commitEntry = QtWidgets.QTextEdit()
        self.commitEntry.setFixedHeight(40)
        self.commitEntry.setPlaceholderText("commit message... ")
        self.commitButton = QtWidgets.QPushButton("Commit")
        self.commitButton.setIcon(Resources.getIcon(":confirm.png"))

        # Commit history section
        self.commitHistory = QtWidgets.QListWidget()
        self.commitHistory.setFixedHeight(120)
        self.commitHistory.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.commitHistory.setAlternatingRowColors(True)
        self.commitHistory.setUniformItemSizes(True)
        self.commitHistory.customContextMenuRequested.connect(self.showCommitContextMenu)

        # setup a file watcher
        self.watcher = QtCore.QFileSystemWatcher()

    def createLayouts(self):
        layout = QtWidgets.QVBoxLayout(self)

        gitRepoLabel = QtWidgets.QLabel("Git Repo:")
        layout.addWidget(gitRepoLabel)

        repoLayout = QtWidgets.QHBoxLayout()
        repoLayout.setContentsMargins(0, 0, 0, 0)
        repoLayout.setSpacing(0)
        repoLayout.addWidget(self.repoLabel)
        repoLayout.addWidget(self.refreshAllButton)
        layout.addLayout(repoLayout)

        layout.addSpacing(10)

        filesChangedLabel = QtWidgets.QLabel("Default Changelist:")
        layout.addWidget(filesChangedLabel)
        layout.addWidget(self.filesChangedList)

        commitLabel = QtWidgets.QLabel("Commit Files:")
        layout.addWidget(commitLabel)
        layout.addWidget(self.commitEntry)
        layout.addWidget(self.commitButton)

        layout.addSpacing(10)

        historyLabel = QtWidgets.QLabel("Commit History:")
        layout.addWidget(historyLabel)
        layout.addWidget(self.commitHistory)

    def createConnections(self):
        self.refreshAllButton.clicked.connect(self.loadFilesChangedSinceLastCommit)
        self.commitButton.clicked.connect(self.commitChanges)
        self.watcher.fileChanged.connect(self.loadFilesChangedSinceLastCommit)

    def setRepo(self, repoPath):
        isInitialized = isRepoInitialized(repoPath)

        if not isInitialized:
            confirmInitialize = mayaMessageBox.MayaMessageBox()
            confirmInitialize.setText("No Git Repo exists")
            confirmInitialize.setHelp()

            confirmInitialize.setInformativeText(f"No Git Repo exists yet. Would you like to initalize one?")
            confirmInitialize.setStandardButtons(
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel
            )

            confirmInitialize.setDefaultButton(QtWidgets.QMessageBox.Save)
            res = confirmInitialize.exec_()

            if res != QtWidgets.QMessageBox.Yes:
                return

            intializeRepo(repo_path=repoPath)

        self.repo = git.Repo(repoPath)
        self.repoLabel.setText(repoPath)
        self.repoLabel.setToolTip(repoPath)

        self.loadCommitHistory()
        self.loadFilesChangedSinceLastCommit()

    def updateWatcherFiles(self, repo):
        if not repo:
            return

        tracked_files = repo.git.ls_files().splitlines()

        for file in tracked_files:
            absoultePath = os.path.join(repo.working_tree_dir, file)
            self.watcher.addPath(absoultePath)

    def loadFilesChangedSinceLastCommit(self):
        # Use git.diff to get both changed and added files since the last commit

        self.filesChangedList.clear()

        # Add the files to the list with appropriate icons (if the head is valid. Otherwise just list untracked files
        if self.repo.head.is_valid():
            for added_file in self.repo.git.diff("HEAD", name_only=True, diff_filter="AM").splitlines():
                self.addFileToChangelist(added_file, icon=":fileModified.png")

            for deleted_file in self.repo.git.diff("HEAD", name_only=True, diff_filter="D").splitlines():
                self.addFileToChangelist(deleted_file, icon=":fileDeleted.png")

        # Also add any untracked files
        untrackedFiles = self.repo.untracked_files
        for untracked_file in untrackedFiles:
            self.addFileToChangelist(untracked_file, icon=":fileAdded.png")

    def addFileToChangelist(self, file, icon):
        item = QtWidgets.QListWidgetItem(file)
        item.setSizeHint(QtCore.QSize(0, ITEM_HEIGHT))  # set height
        item.setIcon(Resources.getIcon(icon))  # Replace with your added file icon path

        differences = self.getDifferencesBetweenLocalAndHead(file)

        lines = differences.split("\n")  # Split the string into lines
        if len(lines) > 35:
            truncated_lines = lines[:35]  # Truncate to the first 10 lines
            differences = "\n".join(truncated_lines)  # Join the truncated lines back into a string
            differences += "\n ... (changes trunicated. Use Print Diff to see all changes)"

        item.setToolTip(differences)

        self.filesChangedList.addItem(item)

    def getDifferencesBetweenLocalAndHead(self, file, printIt=False):
        """
        Get the differences between the current local changes and the latest commit (HEAD) for a specific file.

        :param str file: The path to the file.
        :param bool printIt: print changes made to the file
        :return str : A string describing the differences between local changes and HEAD for the file.
        """
        if not file:
            return

        try:
            # Get the differences between the current local changes and the latest commit (HEAD) for the file
            differences = self.repo.git.diff("HEAD", "--", file)
            if printIt:
                print(differences)
            return differences

        except Exception as e:
            print(f"Error getting differences for {file} between local changes and HEAD: {e}")
            return ""

    def loadCommitHistory(self):
        current_commit = None
        commits = []
        if self.repo.head.is_valid():
            current_commit = self.repo.head.commit
            commits = list(self.repo.iter_commits(max_count=30))

        self.commitHistory.clear()
        for commit in commits:
            commitItem = QtWidgets.QListWidgetItem(f"{commit.hexsha[:7]} {commit.summary}")
            commitItem.setToolTip("\n".join(commit.stats.files))  # Set tooltip with list of files changed
            if commit == current_commit:
                # Use a special icon or marker for the currently active commit
                commitItem.setIcon(Resources.getIcon(":branchActive.png"))
            else:
                # Use a regular commit icon
                commitItem.setIcon(Resources.getIcon(":branch.png"))
            self.commitHistory.addItem(commitItem)

    def commitChanges(self):
        commitMessage = self.commitEntry.toPlainText()

        # Stage changes respecting .gitignore
        self.repo.git.add("--all", ".")

        # Commit the staged changes
        self.repo.index.commit(commitMessage)

        self.commitEntry.clear()
        self.loadCommitHistory()
        self.loadFilesChangedSinceLastCommit()  # Refresh the list of files changed since the last commit
        self.updateWatcherFiles(self.repo)

    def revertToCommit(self, commitId, mode="hard"):
        if mode == "hard":
            title = "Hard Revert Changes"
            message = (
                "Hard Reverting will erease all changes in your default changelist. "
                "Are you sure you want to proceed?"
            )
        else:
            title = "Soft Revert Changes"
            message = (
                "Soft Reverting will move unsaved changes into the default changelist.  "
                "Are you sure you want to proceed?"
            )

        confirmPublishMessage = mayaMessageBox.MayaMessageBox(title=title, message=message, icon="warning")
        confirmPublishMessage.setButtonsYesNoCancel()

        res = confirmPublishMessage.exec_()

        if res == QtWidgets.QMessageBox.Yes:
            if mode == "hard":
                self.repo.git.reset("--hard", commitId)
            else:
                self.repo.git.reset("--soft", commitId)
            self.loadCommitHistory()
            self.loadFilesChangedSinceLastCommit()  # Refresh the list of files changed since the last commit

    def softRevertToCommit(self, commitId):
        self.repo.git.reset("--soft", commitId)
        self.loadCommitHistory()
        self.loadFilesChangedSinceLastCommit()  # Refresh the list of files changed since the last commit

    def showCommitContextMenu(self, pos):
        items = self.commitHistory.selectedItems()
        item = items[0] if items else None

        menu = QtWidgets.QMenu(self.commitHistory)
        revertAction = QtWidgets.QAction(" Hard Revert to Commit", self)
        revertAction.setIcon(Resources.getIcon(":undo_s.png"))

        softRevertAction = QtWidgets.QAction("Soft Revert to Commit", self)
        softRevertAction.setIcon(Resources.getIcon(":undo_s.png"))
        # Extract commit ID
        softRevertAction.triggered.connect(lambda: self.revertToCommit(item.text().split()[0], mode="soft"))
        revertAction.triggered.connect(lambda: self.revertToCommit(item.text().split()[0], mode="hard"))

        menu.addAction(revertAction)
        menu.addAction(softRevertAction)
        menu.exec_(self.commitHistory.mapToGlobal(pos))

    def showFileChangelistContextMenu(self, pos):
        items = self.filesChangedList.selectedItems()
        item = items[0] if items else None

        menu = QtWidgets.QMenu(self.filesChangedList)
        revertFileAction = QtWidgets.QAction("Revert", self)
        revertFileAction.setIcon(Resources.getIcon(":undo_s.png"))

        printDiffAction = QtWidgets.QAction("Print Diff to Script Editor", self)
        printDiffAction.setIcon(Resources.getIcon(":list.svg"))

        addFileToGitIgnore = QtWidgets.QAction("Add File to .gitignore", self)
        addFileToGitIgnore.setIcon(Resources.getIcon(":nodeGrapherClose.png"))

        addDirToGitIgnore = QtWidgets.QAction("Add Dir to .gitignore", self)
        addDirToGitIgnore.setIcon(Resources.getIcon(":nodeGrapherClose.png"))

        revertFileAction.triggered.connect(lambda: self.revertSingleFile(items))
        printDiffAction.triggered.connect(lambda: self.getDifferencesBetweenLocalAndHead(item.text(), printIt=True))
        addFileToGitIgnore.triggered.connect(self.addFileToGitIgnore)
        addDirToGitIgnore.triggered.connect(self.addDirectoryToGitIgnore)

        menu.addAction(revertFileAction)
        menu.addAction(printDiffAction)
        menu.addAction(addFileToGitIgnore)
        menu.addAction(addDirToGitIgnore)
        menu.exec_(self.filesChangedList.mapToGlobal(pos))

    def addFileToGitIgnore(self):
        items = self.filesChangedList.selectedItems()
        if items:
            itemNames = [i.text() for i in items]
            addToGitIgnore(self.repo.working_tree_dir, items_to_ignore=itemNames)
            self.loadFilesChangedSinceLastCommit()

    def addDirectoryToGitIgnore(self):
        items = self.filesChangedList.selectedItems()
        if items:
            item = items[0]
            directory = item.text().rsplit(os.path.sep, 1)[0]
            addToGitIgnore(self.repo.working_tree_dir, items_to_ignore=[directory])
            self.loadFilesChangedSinceLastCommit()

    def revertSingleFile(self, items):
        # Use the `git.checkout` method to revert a single file

        files = [item.text() for item in items]

        for file in files:
            isUntracked = file not in self.repo.untracked_files

            if isUntracked:
                confirmRevert = mayaMessageBox.MayaMessageBox(
                    title=f"Revert Changes to: {file}",
                    message="Reverting will undo all changes. Are you sure you want to proceed?",
                    icon="warning",
                )
                confirmRevert.setButtonsYesNoCancel()

                res = confirmRevert.exec_()

                if res == QtWidgets.QMessageBox.Yes:
                    self.repo.git.checkout(file)
                    print(f"Reverted changes for {file}")
            else:
                confirmDelete = mayaMessageBox.MayaMessageBox(
                    title=f"Delete Untracked File: {file}",
                    message="This file is untracked by Git. Would you like to delete it?",
                    icon="error",
                )
                confirmDelete.setButtonsYesNoCancel()

                res = confirmDelete.exec_()

                if res == QtWidgets.QMessageBox.Yes:
                    absoultePath = os.path.join(self.repo.working_tree_dir, file)
                    os.remove(absoultePath)
                    print(f"Deleted untracked file: {absoultePath}")

            self.loadFilesChangedSinceLastCommit()

    def showEvent(self, event):
        """Setup the watcher"""
        self.updateWatcherFiles(self.repo)

    def closeEvent(self, event):
        # Disable the file watcher when the dialog is closed
        allPaths = self.watcher.files()
        print(f"Removing paths from watcher: {allPaths}")
        self.watcher.removePaths(allPaths)
        event.accept()  # Close the dialog

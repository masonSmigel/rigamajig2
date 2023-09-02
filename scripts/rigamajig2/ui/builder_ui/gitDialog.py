#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    project: rigamajig2
    file: gitDialog.py
    author: masonsmigel
    date: 09/2023
    discription:

"""
import sys
import os
from PySide2 import QtWidgets
from PySide2 import QtGui
from PySide2 import QtCore

import git  # import the gitPython library

from rigamajig2.ui.widgets import mayaDialog, mayaMessageBox
from rigamajig2.shared import common

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
    gitignore_path = os.path.join(repo.working_tree_dir, '.gitignore')

    addToGitIgnore(repo_path, items_to_ignore=["*.DS_Store"])

    # Commit the changes to the repository
    repo.index.add([gitignore_path])
    repo.index.commit(f"Repo intialized")


def addToGitIgnore(repo_path, items_to_ignore):
    repo = git.Repo(repo_path)
    gitignore_path = os.path.join(repo.working_tree_dir, '.gitignore')

    # Check if .gitignore exists; create it if it doesn't
    if not os.path.exists(gitignore_path):
        with open(gitignore_path, 'w') as gitignore_file:
            gitignore_file.write("# .gitignore file\n")

    # Read existing entries from .gitignore
    with open(gitignore_path, 'r') as gitignore_file:
        existing_entries = gitignore_file.read().splitlines()

    # Add new items to .gitignore if they don't already exist
    with open(gitignore_path, 'a') as gitignore_file:
        for item in items_to_ignore:
            if item not in existing_entries:
                gitignore_file.write(f"{item}\n")
                existing_entries.append(item)


class GitDialog(mayaDialog.MayaDialog):
    WINDOW_TITLE = "Git Version History"

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

        # Files Changed Since Last Commit section
        # todo: add the option to add a file/directory from here to the gitIgnore (ie ngSkin files/temp proxies)
        self.filesChangedList = QtWidgets.QListWidget()
        self.filesChangedList.setAlternatingRowColors(True)
        self.filesChangedList.setUniformItemSizes(True)
        self.filesChangedList.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.filesChangedList.customContextMenuRequested.connect(self.showFileChangelistContextMenu)

        # Commit section
        self.commitEntry = QtWidgets.QTextEdit()
        self.commitEntry.setFixedHeight(40)
        self.commitEntry.setPlaceholderText("commit message... ")
        self.commitButton = QtWidgets.QPushButton("Commit")
        self.commitButton.setIcon(QtGui.QIcon(":confirm.png"))

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
        layout.addWidget(self.repoLabel)

        layout.addSpacing(10)

        filesChangedLabel = QtWidgets.QLabel("Files Changed Since Last Commit:")
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
        self.commitButton.clicked.connect(self.commitChanges)
        self.watcher.fileChanged.connect(self.loadFilesChangedSinceLastCommit)

    def setRepo(self, repoPath):
        isInitialized = isRepoInitialized(repoPath)

        if not isInitialized:

            confirmInitialize = mayaMessageBox.MayaMessageBox()
            confirmInitialize.setText("No Git Repo exists")
            confirmInitialize.setHelp()

            confirmInitialize.setInformativeText(
                f"No Git Repo exists yet. Would you like to initalize one?"
                )
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
            for added_file in self.repo.git.diff('HEAD', name_only=True, diff_filter='AM').splitlines():
                self.addFileToChangelist(added_file, icon="git_file_modified.png")

            for deleted_file in self.repo.git.diff('HEAD', name_only=True, diff_filter='D').splitlines():
                self.addFileToChangelist(deleted_file, icon="git_file_deleted.png")

        # Also add any untracked files
        untrackedFiles = self.repo.untracked_files
        for untracked_file in untrackedFiles:
            self.addFileToChangelist(untracked_file, icon="git_file_add.png")

    def addFileToChangelist(self, file, icon):
        item = QtWidgets.QListWidgetItem(file)
        item.setSizeHint(QtCore.QSize(0, ITEM_HEIGHT))  # set height
        item.setIcon(QtGui.QIcon(common.getIcon(icon)))  # Replace with your added file icon path

        differences = self.getDifferencesBetweenLocalAndHead(file)

        lines = differences.split('\n')  # Split the string into lines
        if len(lines) > 35:
            truncated_lines = lines[:35]  # Truncate to the first 10 lines
            differences = '\n'.join(truncated_lines)  # Join the truncated lines back into a string
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
            differences = self.repo.git.diff('HEAD', '--', file)
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
                commitItem.setIcon(QtGui.QIcon(common.getIcon("active_branch_icon.png")))
            else:
                # Use a regular commit icon
                commitItem.setIcon(QtGui.QIcon(common.getIcon("branch_icon.png")))
            self.commitHistory.addItem(commitItem)

    def commitChanges(self):
        commitMessage = self.commitEntry.toPlainText()

        # Stage changes respecting .gitignore
        self.repo.git.add('--all', '.')

        # Commit the staged changes
        self.repo.index.commit(commitMessage)

        self.commitEntry.clear()
        self.loadCommitHistory()
        self.loadFilesChangedSinceLastCommit()  # Refresh the list of files changed since the last commit
        self.updateWatcherFiles(self.repo)

    def revertToCommit(self, commitId, mode="hard"):

        confirmPublishMessage = mayaMessageBox.MayaMessageBox()
        confirmPublishMessage.setText("Revert Changes")
        confirmPublishMessage.setWarning()

        confirmPublishMessage.setInformativeText(
            "Reverting will undo all changes that are not saved into a commit. Are you sure you want to proceed?"
            )
        confirmPublishMessage.setStandardButtons(
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel
            )

        confirmPublishMessage.setDefaultButton(QtWidgets.QMessageBox.Save)
        res = confirmPublishMessage.exec_()

        if res == QtWidgets.QMessageBox.Yes:
            if mode == "hard":
                self.repo.git.reset('--hard', commitId)
            else:
                self.repo.git.reset('--soft', commitId)
            self.loadCommitHistory()
            self.loadFilesChangedSinceLastCommit()  # Refresh the list of files changed since the last commit

    def softRevertToCommit(self, commitId):

        self.repo.git.reset('--soft', commitId)
        self.loadCommitHistory()
        self.loadFilesChangedSinceLastCommit()  # Refresh the list of files changed since the last commit

    def showCommitContextMenu(self, pos):
        item = self.commitHistory.selectedItems()[0]
        if item:
            menu = QtWidgets.QMenu(self.commitHistory)
            revertAction = QtWidgets.QAction(" Hard Revert to Commit", self)
            revertAction.triggered.connect(
                lambda: self.revertToCommit(item.text().split()[0], mode="hard"))  # Extract commit ID

            softRevertAction = QtWidgets.QAction("Soft Revert to Commit", self)
            softRevertAction.triggered.connect(
                lambda: self.revertToCommit(item.text().split()[0], mode="soft"))  # Extract commit ID

            menu.addAction(revertAction)
            menu.addAction(softRevertAction)
            menu.exec_(self.commitHistory.mapToGlobal(pos))

    def showFileChangelistContextMenu(self, pos):
        items = self.filesChangedList.selectedItems()
        item = items[0] if items else None

        menu = QtWidgets.QMenu(self.filesChangedList)
        revertFileAction = QtWidgets.QAction("Revert", self)
        printDiffAction = QtWidgets.QAction("Print Diff to Script Editor", self)
        addFileToGitIgnore = QtWidgets.QAction("Add File to .gitignore", self)
        addDirToGitIgnore = QtWidgets.QAction("Add Dir to .gitignore", self)

        revertFileAction.triggered.connect(lambda: self.revertSingleFile(item.text()))
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

    def revertSingleFile(self, file):
        # Use the `git.checkout` method to revert a single file

        isUntracked = file not in self.repo.untracked_files

        if isUntracked:
            confirmRevert = mayaMessageBox.MayaMessageBox()
            confirmRevert.setText(f"Revert Changes to: {file}")
            confirmRevert.setWarning()

            confirmRevert.setInformativeText(
                "Reverting will undo all changes that are not saved into a commit. Are you sure you want to proceed?"
                )
            confirmRevert.setStandardButtons(
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel
                )

            confirmRevert.setDefaultButton(QtWidgets.QMessageBox.Save)
            res = confirmRevert.exec_()

            if res == QtWidgets.QMessageBox.Yes:
                self.repo.git.checkout(file)
                print(f"Reverted changes for {file}")
        else:
            confirmDelete = mayaMessageBox.MayaMessageBox()
            confirmDelete.setText(f"Delete Untracked File: {file}")
            confirmDelete.setError()

            confirmDelete.setInformativeText(
                "This file is untracked by Git. Would you like to delete it?"
                )
            confirmDelete.setStandardButtons(
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel
                )

            confirmDelete.setDefaultButton(QtWidgets.QMessageBox.Save)
            res = confirmDelete.exec_()

            if res == QtWidgets.QMessageBox.Yes:
                absoultePath = os.path.join(self.repo.working_tree_dir, file)
                os.remove(absoultePath)
                print(f"Deleted untracked file: {absoultePath}")

            self.loadFilesChangedSinceLastCommit()

    def showEvent(self, event):
        """ Setup the watcher"""

        self.updateWatcherFiles(self.repo)

    def closeEvent(self, event):
        # Disable the file watcher when the dialog is closed
        allPaths = self.watcher.files()
        print(f"Removing paths from watcher: {allPaths}")
        self.watcher.removePaths(allPaths)
        event.accept()  # Close the dialog

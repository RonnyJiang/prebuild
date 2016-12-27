import os


class CommentsList(object):

    """ Stores comments, that can be later used utilized
    by Change::setReview """

    comments = {}

    def __init__(self):
        pass

    def addComment(self, path, line, message):
        if path in self.comments:
            self.comments[path].append({"line": line, "message": message})
        else:
            self.comments[path] = [{"line": line, "message": message}]

    def clear(self):
        self.comments.clear()

    def getCommentsList(self):
        return self.comments


class Change(object):
    changeInfo = None
    conn = None
    changeURL = None

    def __init__(self, conn, changeId):
        self.conn = conn
        self.changeInfo = self.conn.GET("a/changes/?q=" + changeId + "&o=CURRENT_REVISION&o=DOWNLOAD_COMMANDS")[0]
        self.changeURL = os.path.join("a/changes/", self.changeInfo["id"])

    def rebase(self):
        address = os.path.join(self.changeURL, "rebase")
        return self.conn.POST(address)

    def createDraft(self, path, line, message):
        address = os.path.join(self.changeURL, "revisions", "current", "drafts")
        data = {"path": path, "line": line, "message": message}
        return self.conn.PUT(address, data)

    def setReview(self, message, codeReview, verified, comments=CommentsList()):
        address = os.path.join(self.changeURL, "revisions/current/review")
        data = {"message": message,
                "labels": {"Code-Review": codeReview, "Verified": verified},
                "comments": comments.getCommentsList()}
        return self.conn.POST(address, data)

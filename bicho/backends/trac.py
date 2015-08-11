# -*- coding: utf-8 -*-
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# Authors:  Rodrigo Primo <rodrigosprimo@gmail.com>
#

from bicho.config import Config
from bicho.backends import Backend
from bicho.common import Issue, Tracker, People
from bicho.utils import printdbg, printerr, printout
from bicho.db.database import DBIssue, DBBackend, get_database
from storm.locals import Int, Reference
import xmlrpclib
import sys
import dateutil.parser


class DBTracIssueExt(object):
    """
    Types for each field.
    """
    __storm_table__ = 'issues_ext_trac'

    id = Int(primary=True)
    issue_id = Int()
    issue = Reference(issue_id, DBIssue.id)

    def __init__(self, issue_id):
        self.issue_id = issue_id

class DBTracIssueExtMySQL(DBTracIssueExt):
    """
    MySQL subclass of L{DBTracIssueExt}
    """
    __sql_table__ = 'CREATE TABLE IF NOT EXISTS issues_ext_trac (\
                     id INTEGER NOT NULL AUTO_INCREMENT, \
                     issue_id INTEGER NOT NULL, \
                     PRIMARY KEY(id), \
                     UNIQUE KEY(issue_id), \
                     INDEX ext_issue_idx(issue_id), \
                     FOREIGN KEY(issue_id) \
                       REFERENCES issues(id) \
                         ON DELETE CASCADE \
                         ON UPDATE CASCADE \
                     ) ENGINE=MYISAM; '

class DBTracBackend(DBBackend):
    """
    Adapter for Trac backend, to make it so there is a MYSQL_EXT.
    """
    def __init__(self):
        self.MYSQL_EXT = [DBTracIssueExtMySQL]

    def insert_issue_ext(self, store, issue, issue_id):
        """
        Insert the given extra parameters of issue with id X{issue_id}.

        @param store: database connection
        @type store: L{storm.locals.Store}
        @param issue: issue to insert
        @type issue: L{TracIssue}
        @param issue_id: identifier of the issue
        @type issue_id: C{int}

        @return: the inserted extra parameters issue
        @rtype: L{DBTracIssueExt}
        """

        newIssue = False

        try:
            db_issue_ext = store.find(DBTracIssueExt,
                                      DBTracIssueExt.issue_id
                                      ==
                                      issue_id).one()
            if not db_issue_ext:
                newIssue = True
                db_issue_ext = DBTracIssueExt(issue_id)

            if newIssue == True:
                store.add(db_issue_ext)

            store.flush()
            return db_issue_ext
        except:
            store.rollback()
            raise

class TracBackend(Backend):

    def __init__(self):
        self.url = Config.url

    def get_issue_data(self, issue):
        """Create an Issue object from the data returned by Trac API."""
        
        printdbg("analyzing a new issue")
        
        bugid = issue[0]
        summary = issue[3]['summary']
        bugtype = issue[3]['type']
        description = issue[3]['description']
        submitted_on = dateutil.parser.parse(issue[1].value)
        author = People(issue[3]['reporter'])
        
        issue = Issue(bugid, bugtype, summary, description, author, submitted_on)
        
        return issue

    def run(self):       
        print("Running Bicho")

        issuesdb = get_database(DBTracBackend())
        printdbg(self.url)

        trac = xmlrpclib.ServerProxy(self.url)
        multicall = xmlrpclib.MultiCall(trac)
        tickets = trac.ticket.query()
        
        for issue_id in tickets:
            multicall.ticket.get(issue_id)
            
        issues = multicall()

        issuesdb.insert_supported_traker("trac", "1.0")
        trk = Tracker(self.url, "trac", "1.0")
        dbtrk = issuesdb.insert_tracker(trk)

        nissues = len(issues.results)
        
        if nissues == 0:
            printout("No issues found. Did you provide the correct URL?")
            sys.exit(0)

        for issue in issues.results:
            try:
                issue_data = self.get_issue_data(issue[0])
                printout("Analyzing issue # %s" % issue[0][0])
            except Exception:
                printerr("Error in function get_issue_data with Bug: %s" % issue[0])
                raise

            issuesdb.insert_issue(issue_data, dbtrk.id)

        try:
            # we read the temporary table with the relationships and create
            # the final one
            issuesdb.store_final_relationships()
        except:
            raise

        printout("Done. %s issues analyzed" % (nissues))
        
Backend.register_backend("trac", TracBackend)

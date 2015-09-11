# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Bitergia
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
# Authors:  Santiago Dueñas <sduenas@bitergia.com>
#

import requests

from bicho.backends import Backend
from bicho.backends.trac import Trac, TracRPC


class TracWordPress(Trac):
    def __init__(self):
        Trac.__init__(self)
        
        self.trac_rpc = TracRPCWordPress(self.url)
        
class TracRPCWordPress(TracRPC):
    def __init__(self, url):
        TracRPC.__init__(self, url)
        
        self.requests = requests.Session()
        login_url = 'https://wordpress.org/support/bb-login.php'
        login_data = {'password': self.backend_password, 'user_login': self.backend_user}
        
        self.requests.post(login_url, login_data)

Backend.register_backend('trac_wordpress', TracWordPress)

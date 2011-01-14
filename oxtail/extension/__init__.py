from crx import *
from xpi import *

class UserScriptExtension(CrxExtension, XpiExtension):
    def get_crx_files(self):
        out = super(UserScriptExtension, self).get_crx_files()
        out['user.js'] = self.get_user_script()
        return out
    
    def get_crx_manifest(self):
        out = super(UserScriptExtension, self).get_crx_manifest()
        out['content_scripts'] = [
            {
                'exclude_globs': [],
                'include_globs': [],
                'js': ['user.js'],
                'matches': getattr(self, 'matches', [])
            }
        ]
        return out
    
    def get_user_script(self):
        return ""
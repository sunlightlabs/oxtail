# This XPI-generating code is mostly a port/adaptation of this PHP Greasemonkey
# userscript compiler: http://arantius.com/misc/greasemonkey/script-compiler.phps
# which, in turn, incorporates a bunch of code from Greasemonkey proper.

from django.template import Context, Template
import zipfile
import dircache
import re
import uuid
import os
import io

def make_zip(z, path, parent, data):
    for ch in dircache.listdir(path):
        child = os.path.join(path, ch)
        name = "%s/%s" % (parent, ch) if parent else ch
        if os.path.isfile(child): z.writestr(name, Template(open(child).read()).render(Context(data)))
        if os.path.isdir(child): make_zip(z, child, name, data)

def rewrite_matches(matches, negate=False):
    if matches:
        regs = map(lambda m: '/%s/.test(href)' % m.replace('/', '\\/').replace('*', '.*'), matches)
        reg_string = '%s( %s )' % (
            '!' if negate else '',
            ' || '.join(regs)
        )
        return reg_string
    else:
        return 'true'

class XpiExtension(object):
    def get_xpi_manifest(self):
        if not hasattr(self, 'xpi_manifest'):
            out = {
                'id': getattr(self, 'id', '{%s}' % str(uuid.uuid4())),
                'name': getattr(self, 'name', 'Some Extension'),
                'version': getattr(self, 'version', '0.1'),
                'description': getattr(self, 'description', 'sample extension'),
                'creator': getattr(self, 'creator', ''),
                'homepage': getattr(self, 'homepage', ''),
                'include': rewrite_matches(getattr(self, 'matches', [])),
                'exclude': rewrite_matches(getattr(self, 'exclude', []), True),
                'min_version': getattr(self, 'FF_min_version', '1.5'),
                'max_version': getattr(self, 'FF_max_version', '4.0.*'),
            }
            out['shortname'] = re.sub('[^a-zA-Z]', '', out['name'])
            self.xpi_manifest = out
        return self.xpi_manifest
    
    def get_xpi_extra_files(self):
        manifest = self.get_xpi_manifest()
        out = {'content/%s.js' % manifest['shortname']: self.get_user_script()}
        return out
    
    def get_user_script(self):
        return ''
    
    def get_xpi_extra_file_contents(self):
        files = self.get_xpi_extra_files()
        out = {}
        
        for filename in files:
            if getattr(files[filename], 'read', False):
                contents = files[filename].read()
            elif getattr(files[filename], '__call__', False):
                contents = files[filename].__call__()
            else:
                contents = files[filename]
            
            out[filename] = contents
        
        return out
    
    def gen_xpi(self, out):
        if not getattr(out, 'write', False):
            out = open(out, 'w')
        
        extra_files = self.get_xpi_extra_file_contents()
        zip_memory = io.BytesIO()
        zip = zipfile.ZipFile(zip_memory, "w", zipfile.ZIP_DEFLATED)
        
        make_zip(zip, os.path.join(os.path.dirname(__file__), 'xpi_base'), '', self.get_xpi_manifest())
        
        for filename in extra_files:
            zip.writestr(filename, extra_files[filename])
        zip.close()
        zip_data = zip_memory.getvalue()
        
        out.write(zip_data)
        
        return out
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
import time
from Crypto.PublicKey import RSA
from django.conf import settings
import hashlib
import subprocess
import base64

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

_fixed_date = getattr(settings, 'ZIP_DATE', time.struct_time((2011, 1, 1, 0, 0, 0, 5, 1, 0)))

def make_zip(z, path, parent, data):
    for ch in dircache.listdir(path):
        child = os.path.join(path, ch)
        name = "%s/%s" % (parent, ch) if parent else ch
        if os.path.isfile(child): z.writestr(zipfile.ZipInfo(name, _fixed_date), str(Template(open(child).read()).render(Context(data))))
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
                'max_version': getattr(self, 'FF_max_version', '8.0.*'),
                'update_url': getattr(self, 'FF_update_url', ''),
                'download_url': getattr(self, 'FF_download_url', ''),
            }
            out['shortname'] = re.sub('[^a-zA-Z]', '', out['name'])
            
            # generate update key
            pem_name = getattr(self, 'pem_path', None)
            if pem_name:
                key_file = open(pem_name, 'r')
                private_pem = key_file.read()
                key_file.close()
                
                pkey = RSA.importKey(private_pem)
                
                public = pkey.publickey().exportKey('PEM').split('\n')[1:-1]
                out['update_key'] = ''.join(public)
            
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
            zip.writestr(zipfile.ZipInfo(filename, _fixed_date), str(extra_files[filename]))
        zip.close()
        zip_data = zip_memory.getvalue()
        
        out.write(zip_data)
        
        return out
    
    def gen_xpi_update_rdf(self, out):
        xpi_data = StringIO()
        self.gen_xpi(xpi_data)
        
        update_hash = hashlib.sha1(xpi_data.getvalue()).hexdigest()
        
        properties = {}
        properties.update(self.get_xpi_manifest())
        properties.update({'update_hash': update_hash})
        
        updates = os.path.join(os.path.dirname(__file__), 'xpi_updates')
        normalized = str(Template(open(os.path.join(updates, 'update_normalized.rdf')).read()).render(Context(properties)))
        openssl_signer = subprocess.Popen(['openssl', 'dgst', '-sha512', '-hex', '-sign', getattr(self, 'pem_path', None)], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        sig = openssl_signer.communicate(normalized)[0].strip()
        
        RSA = ASN1Algorithm()
        RSA.setComponentByName('oid', (1, 2, 840, 113549, 1, 1, 13))
        asn1sig = ASN1Signature()
        asn1sig.setComponentByName('alg', RSA)
        asn1sig.setComponentByName('seq', "'%s'H" % sig)
        
        rdf_signature = base64.b64encode(encoder.encode(asn1sig))
        
        properties.update({'rdf_signature': rdf_signature})
        out.write(str(Template(open(os.path.join(updates, 'update.rdf')).read()).render(Context(properties))))

# some ASN1 utility classes
from pyasn1.type import univ, namedtype, namedval, constraint
from pyasn1.codec.der import encoder

class ASN1Algorithm(univ.Sequence):
    componentType = namedtype.NamedTypes(
        namedtype.NamedType('oid', univ.ObjectIdentifier()),
        namedtype.OptionalNamedType('opt', univ.Any())
    )

class ASN1Signature(univ.Sequence):
    componentType = namedtype.NamedTypes(
        namedtype.NamedType('alg', ASN1Algorithm()),
        namedtype.NamedType('seq', univ.BitString())
    )

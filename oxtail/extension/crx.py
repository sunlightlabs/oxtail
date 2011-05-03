import hashlib
import io
import os
import struct
import subprocess
import sys
import zipfile
import json
from Crypto.PublicKey import RSA
import subprocess
from django.template import Context, Template

class CrxExtension(object):
    def get_crx_manifest(self):
        return {
            'name': getattr(self, 'name', 'Some Extension'),
            'version': getattr(self, 'version', '0.1'),
            'description': getattr(self, 'description', 'sample extension'),
            'homepage_url': getattr(self, 'homepage', ''),
            'update_url': getattr(self, 'GC_update_url', '')
        }
    
    def get_crx_files(self):
        return {
            'manifest.json': json.dumps(self.get_crx_manifest()),
        }
    
    def get_crx_file_contents(self):
        files = self.get_crx_files()
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
    
    def get_crx_key(self):
        pem_name = getattr(self, 'pem_path', None)
        if pem_name:
            key_file = open(pem_name, 'r')
            private_pem = key_file.read()
            key_file.close()
            
            pkey = RSA.importKey(private_pem)
        else:
            pkey = RSA.generate(1024)
            pem_name = '/tmp/key_%s.pem' % pkey.exportKey(format='PEM').split('\n')[1][-10:]
            key_file = open(pem_name, 'w')
            key_file.write(pkey.exportKey(format='PEM'))
        
        return (pem_name, pkey)
    
    def gen_crx(self, out):
        # borrows liberally from https://github.com/bellbind/crxmake-python/blob/master/crxmake.py
        
        if not getattr(out, 'write', False):
            out = open(out, 'w')
            
        files = self.get_crx_file_contents()
        zip_memory = io.BytesIO()
        zip = zipfile.ZipFile(zip_memory, "w", zipfile.ZIP_DEFLATED)
        
        for filename in files:
            zip.writestr(filename, files[filename])
        zip.close()
        zip_data = zip_memory.getvalue()
        
        pem_name, pkey = self.get_crx_key()
        
        # I couldn't actually get pycrypto to generate the right thing, here, so I'm calling OpenSSL to do it
        openssl_signer = subprocess.Popen(['openssl', 'sha1', '-sha1', '-binary', '-sign', pem_name], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        sign = openssl_signer.communicate(zip_data)[0]
        
        der_key = pkey.publickey().exportKey(format='DER')
        magic = 'Cr24'
        version = struct.pack("<I", 2)
        key_len = struct.pack("<I", len(der_key))
        sign_len = struct.pack("<I", len(sign))
        
        out.write(magic)
        out.write(version)
        out.write(key_len)
        out.write(sign_len)
        out.write(der_key)
        out.write(sign)
        out.write(zip_data)
        
        return out
    
    def gen_crx_update_xml(self, out):
        # determine extension ID
        pem_name, pkey = self.get_crx_key()
        public = pkey.publickey().exportKey(format='DER')
        hash = hashlib.sha256(public).hexdigest()[:32]
        adjusted_hash = [chr(d) for d in [c + 49 if c < 97 else c + 10 for c in [ord(a) for a in hash]]]
        id = ''.join(adjusted_hash)
        
        properties = {'appid': id, 'download_url': getattr(self, 'GC_download_url', ''), 'version': getattr(self, 'version', '0.1')}
        
        updates = os.path.join(os.path.dirname(__file__), 'crx_updates')
        out.write(str(Template(open(os.path.join(updates, 'update.xml')).read()).render(Context(properties))))

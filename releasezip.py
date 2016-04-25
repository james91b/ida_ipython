import os
import sys
import zipfile

def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))
            
def main(version) :
    release = zipfile.ZipFile('release-{}.zip'.format(version), 'w')
    zipdir('python', release)
    zipdir('idc', release)
    zipdir('notebook', release)
    release.write('build/release/ida_ipython.p64', 'plugins/ida_ipython.p64')
    release.write('build/release/ida_ipython.plw', 'plugins/ida_ipython.plw')
    release.write('README.md')
    release.close()
    
if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print "No release name provided"
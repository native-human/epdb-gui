INSTALLDIR=debian/usr/bin
IMAGEDIR=debian/usr/share/gepdb/
PACKAGEDIR=debian/usr/lib/pymodules/python2.6/gepdb
mkdir -p ${INSTALLDIR}
mkdir -p ${IMAGEDIR}
mkdir -p ${PACKAGEDIR}
cp breakpoint.png ${IMAGEDIR}
cp gepdb.py ${INSTALLDIR}/gepdb
cp gepdb/*.py ${PACKAGEDIR}
python -mcompileall ${PACKAGEDIR}
dpkg-deb --build debian
mv debian.deb gepdb.deb

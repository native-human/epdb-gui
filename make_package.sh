INSTALLDIR=debian/usr/bin
IMAGEDIR=debian/usr/share/gepdb/
PACKAGEDIR=debian/usr/lib/pymodules/python2.6/gepdb
MAN1DIR=debian/usr/share/man/man1
mkdir -p ${INSTALLDIR}
mkdir -p ${IMAGEDIR}
mkdir -p ${PACKAGEDIR}
mkdir -p ${MAN1DIR}
cp breakpoint.png ${IMAGEDIR}
cp bug.png ${IMAGEDIR}
cp gepdb.py ${INSTALLDIR}/gepdb
cp gepdb/*.py ${PACKAGEDIR}
cp doc/gepdb.nroff ${MAN1DIR}/gepdb.1
gzip -f -9 ${MAN1DIR}/gepdb.1
python -mcompileall ${PACKAGEDIR}
fakeroot dpkg-deb --build debian
mv debian.deb gepdb.deb

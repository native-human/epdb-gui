INSTALLDIR=debian/usr/bin
IMAGEDIR=debian/usr/share/gepdb/
mkdir -p ${INSTALLDIR}
mkdir -p ${IMAGEDIR}
cp breakpoint.png ${IMAGEDIR}
cp gepdb.py ${INSTALLDIR}/gepdb
dpkg-deb --build debian
mv debian.deb gepdb.deb

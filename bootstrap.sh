#!/bin/sh

## @ŧodo Check CPU architecture!

# Set exit on error.
set -e

#
# Cleanup first.
## @todo Warn before doing this!
#
umount opt
rm -rf /volume1/@optware
rm -rf /usr/lib/ipkg

#
# Install Entware.
# See: https://github.com/Entware/entware
#
ENTWARE_PACKAGES="
    bash
    bash-completion
    bzip2
    coreutils-md5sum
    coreutils-mktemp
    coreutils-sha1sum
    coreutils-sha256sum
    coreutils-sha512sum
    cryptsetup
    curl
    git
    htop
    less
    lsof
    mc
    ncdu
    screen
    rsync
    rsnapshot
    smartmontools
    strace
    subversion-client
    vim
    wget"

PATH_ENTWARE_ROOT=/Apps/opt
mkdir -p /Apps
mkdir -p /volume1/@qnapware/opt
ln -s /volume1/@qnapware/opt $PATH_ENTWARE_ROOT
cd /volume1/@qnapware/opt
wget -O - http://qnapware.zyxmon.org/binaries-arm/installer/qnapware_install_arm.sh | sh
PATH_ENTWARE=$PATH_ENTWARE_ROOT/bin:$PATH_ENTWARE_ROOT/sbin:$PATH_ENTWARE_ROOT/local/bin:$PATH_ENTWARE_ROOT/local/sbin
export PATH_ORG=$PATH
export PATH=$PATH_ENTWARE:$PATH
$PATH_ENTWARE_ROOT/bin/opkg update
$PATH_ENTWARE_ROOT/bin/opkg install ${ENTWARE_PACKAGES}

#
# Install Optware.
# Note: Only use Optware where absolutely necessary, as it contains a lot of old and outdated
#       stuff we don't want on our servers (anymore). For everything else we'll use Entware (see above).
cd /tmp
wget -O - http://ipkg.nslu2-linux.org/feeds/optware/cs08q1armel/cross/stable/syno-mvkw-bootstrap_1.2-7_arm.xsh | sh
# Patch the bootstrap script to also recognize newer Kirkwood CPUs.
sed -i -e "s/Feroceon-KW/Feroceon/g" /tmp/bootstrap/bootstrap.sh
# Re-execute the (patched) bootstrap script.
sh /tmp/bootstrap/bootstrap.sh
#  Update sources.
/opt/bin/ipkg update
rm -rf /tmp/bootstrap

#
# Install the stuff we need from Optware.
#
/opt/bin/ipkg install py26-rdiff-backup
ln -s /opt/bin/rdiff-backup-2.6 /usr/bin/rdiff-backup
ln -s /opt/bin/rdiff-backup-statistics-2.6 /usr/bin/rdiff-backup-statistics

#
# Make sure that Optware + Entware start their stuff.
#
cat <<EOT >> /etc/rc.local
#!/bin/sh

# Optware setup
[ -x /etc/rc.optware ] /etc/rc.optware start

# Entware setup
/bin/mkdir -p /Apps
/bin/ln -sf /volume1/@qnapware/opt /Apps/opt
/Apps/opt/etc/init.d/rc.unslung start
exit 0
EOT

#
# Tweak /etc.
#
chmod -R u=rwX,g=rwX,o=rX * /etc
chmod -R u=rw,go= * /etc/ssh

# Replace ash with bash.
PATH_SHELL_OLD=/bin/ash
PATH_SHELL_NEW=/Apps/opt/bin/bash
sed -i -e "s|$PATH_SHELL_OLD|$PATH_SHELL_NEW|g" /etc/passwd

#
# Install additional CA-Certs. Currently none are required.
#
CA_CERTS=""

for CERT in $CA_CERTS
do
    echo "Installing $CERT ..."
    cd /tmp
    wget $CERT
    CERT_NAME_CRT=$(basename $CERT)
    cp $CERT_NAME_CRT /usr/share/ca-certificates/mozilla/$CERT_NAME
    CERT_NAME_PEM=$(basename $CERT_NAME_CRT .crt).pem
    ln -s /usr/share/ca-certificates/mozilla/$CERT_NAME_CRT /etc/ssl/certs/$CERT_NAME_PEM
    cd /etc/ssl/certs
    ln -s CERT_NAME_PEM.pem `openssl x509 -hash -noout -in $CERT_NAME_PEM`.0
    openssl verify -CApath /etc/ssl/certs $CERT_NAME_PEM
done

#
# Do some other required hacks.
#

# Link some more binaries to the /bin directory. Required e.g. for
# a shebang. Everything else though should be in $PATH anyway.
ln -s /Apps/opt/bin/bash /bin/bash
ln -s /Apps/opt/bin/mktemp /bin/mktemp

# Set the correct OpenSSL config.
rm /opt/share/openssl/openssl.cnf
ln -s /etc/ssl/openssl.cnf /opt/share/openssl/openssl.cnf

# Let CURL and friends find the CACerts.
ln -s /etc/ssl /Apps/opt/etc/ssl
ln -s /etc/ssl /opt/etc/ssl

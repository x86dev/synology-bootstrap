#!/bin/sh

## @ŧodo Check architecture!

#
# Install Entware.
# See: https://github.com/Entware/entware
#
PATH_ENTWARE_ROOT=/Apps/opt &&
mkdir -p /Apps &&
mkdir -p /volume1/@qnapware/opt &&
ln -s /volume1/@qnapware/opt $PATH_ENTWARE_ROOT &&
cd /volume1/@qnapware/opt &&
wget -O - http://qnapware.zyxmon.org/binaries-arm/installer/qnapware_install_arm.sh | sh &&
PATH_ENTWARE=$PATH_ENTWARE_ROOT/bin:$PATH_ENTWARE_ROOT/sbin:$PATH_ENTWARE_ROOT/local/bin:$PATH_ENTWARE_ROOT/local/sbin &&
export PATH_ORG=$PATH &&
export PATH=$PATH_ENTWARE:$PATH &&
opkg install bash bash-completion bzip2 cryptsetup git htop less lsof mc ncdu screen rsync rsnapshot smartmontools strace subversion-client vim wget

#
# Make sure that Optware + Entware start their stuff.
#
cat <<EOT >> /etc/rc.local
#!/bin/sh

# Optware setup
[ -x /etc/rc.optware ] && /etc/rc.optware start

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

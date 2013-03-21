#!/usr/bin/env bash

# Upgrade parameters
ProductName=hornetq
SourceURL=http://www.silverpeas.org/files/hornetq-upgrade-latest.tar.bz2
DestinationPath="${JBOSS_HOME}"
FileToCompare=common/lib/hornetq-core.jar

## Upgrade generic process.

# Compare the actual version of the product with the expected one.
# Waits for two arguments:
# $1 the actual version of the product
# $2 the expected version of the product (id est the last one)
# Returns 0 if the two versions of the product are equal, 1 otherwise.
function compare {
  actual="$1"
  expected="$2"
  md5sum "$actual" > /tmp/${ProductName}.actual
  md5sum "$expected" > /tmp/${ProductName}.expected
  diff /tmp/${ProductName}.actual /tmp/${ProductName}.expected > /dev/null 2>&1
  result=$?
  rm /tmp/${ProductName}.actual /tmp/${ProductName}.expected
  return $result
}

# Upgrades the version of the product.
# Waits for two arguments:
# $1 the path of the directory where is located the new version of the product.
# Exits the script if the upgrade fails.
function upgrade {
  src="$1"
  alldirs=`find ${src} -type d`
  for dir in ${alldirs}; do
    for lib in `ls ${dir}`; do
      file ${dir}/${lib} | grep directory > /dev/null
      test $? -eq 0 && continue
      rm -rf ${DestinationPath}/${dir##${src}}/${lib}
      cp ${dir}/${lib} ${DestinationPath}/${dir##${src}}/
      test $? -eq 0 || return 1
    done
  done
  return $?
}

# Fetch the last version of the product
InstallDir=/tmp/${ProductName}
mkdir -p ${InstallDir}
wget ${SourceURL} -P ${InstallDir}
tar jxvf ${InstallDir}/*.tar.bz2 -C ${InstallDir} > /dev/null
rm ${InstallDir}/*.tar.bz2
ProductHome=${InstallDir}/`ls ${InstallDir}`

# Check the last version is a newer than the current one.
compare "${DestinationPath}/${FileToCompare}" "${ProductHome}/${FileToCompare}"
test $? -eq 0 && exit 0

# Upgrade the product
echo "New version of ${ProductName} detected, upgrade it..."
upgrade "${ProductHome}" "."
res=$?
rm -rf ${InstallDir} > /dev/null 2>&1
test $res -eq 0 && echo "Upgrade of ${ProductName} succeeded"
test $res -ne 0 && echo "Upgrade of ${ProductName} failed"
exit $res

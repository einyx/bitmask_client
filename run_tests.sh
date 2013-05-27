#!/bin/bash

set -eu

function usage {
  echo "Usage: $0 [OPTION]..."
  echo "Run leap-client test suite"
  echo ""
  echo "  -V, --virtual-env        Always use virtualenv.  Install automatically if not present"
  echo "  -N, --no-virtual-env     Don't use virtualenv.  Run tests in local environment"
  echo "  -s, --no-site-packages   Isolate the virtualenv from the global Python environment"
  echo "  -x, --stop               Stop running tests after the first error or failure."
  echo "  -f, --force              Force a clean re-build of the virtual environment. Useful when dependencies have been added."
  echo "  -p, --pep8               Just run pep8"
  echo "  -P, --no-pep8            Don't run pep8"
  echo "  -c, --coverage           Generate coverage report"
  echo "  -h, --help               Print this usage message"
  echo "  -A, --all		   Run all tests, without excluding any"
  echo "  -i, --progressive	   Run with nose-progressive plugin"
  echo "  --hide-elapsed           Don't print the elapsed time for each test along with slow test list"
  echo ""
  echo "Note: with no options specified, the script will try to run the tests in a virtual environment,"
  echo "      If no virtualenv is found, the script will ask if you would like to create one.  If you "
  echo "      prefer to run tests NOT in a virtual environment, simply pass the -N option."
  exit
}

function process_option {
  case "$1" in
    -h|--help) usage;;
    -V|--virtual-env) always_venv=1; never_venv=0;;
    -N|--no-virtual-env) always_venv=0; never_venv=1;;
    -s|--no-site-packages) no_site_packages=1;;
    -f|--force) force=1;;
    -p|--pep8) just_pep8=1;;
    -P|--no-pep8) no_pep8=1;;
    -c|--coverage) coverage=1;;
    -A|--all) alltests=1;;
    -i|--progressive) progressive=1;;
    -*) noseopts="$noseopts $1";;
    *) noseargs="$noseargs $1"
  esac
}

venv=.venv
with_venv=pkg/tools/with_venv.sh
always_venv=0
never_venv=0
force=0
no_site_packages=0
installvenvopts=
noseargs=
noseopts=
wrapper=""
just_pep8=0
no_pep8=0
coverage=0
alltests=0
progressive=0

for arg in "$@"; do
  process_option $arg
done

# If enabled, tell nose to collect coverage data
if [ $coverage -eq 1 ]; then
    noseopts="$noseopts --with-coverage --cover-package=leap-client"
fi

if [ $no_site_packages -eq 1 ]; then
  installvenvopts="--no-site-packages"
fi

# If alltests flag is not set, let's exclude some dirs that are troublesome.
if [ $alltests -eq 0 ]; then
  echo "[+] Running ALL tests..."
  #noseopts="$noseopts --exclude-dir=leap/soledad"
fi

# If progressive flag enabled, run with this nice plugin :)
if [ $progressive -eq 1 ]; then
    noseopts="$noseopts --with-progressive"
fi


function run_tests {
  # Just run the test suites in current environment
  ${wrapper} $NOSETESTS
  # If we get some short import error right away, print the error log directly
  RESULT=$?
  return $RESULT
}

function run_pep8 {
  echo "Running pep8 ..."
  srcfiles="src/leap"
  # Just run PEP8 in current environment
  pep8_opts="--ignore=E202,W602 --exclude=*_rc.py,ui_*,_version.py --repeat"
  ${wrapper} pep8 ${pep8_opts} ${srcfiles}
}

# XXX we cannot run tests that need X server
# in the current debhelper build process,
# so I exclude the topmost tests

NOSETESTS="nosetests leap --first-package-wins --exclude=soledad* $noseopts $noseargs"

if [ $never_venv -eq 0 ]
then
  # Remove the virtual environment if --force used
  if [ $force -eq 1 ]; then
    echo "Cleaning virtualenv..."
    rm -rf ${venv}
  fi
  if [ -e ${venv} ]; then
    wrapper="${with_venv}"
  else
    if [ $always_venv -eq 1 ]; then
      # Automatically install the virtualenv
      python pkg/install_venv.py $installvenvopts
      wrapper="${with_venv}"
    else
      echo -e "No virtual environment found...create one? (Y/n) \c"
      read use_ve
      if [ "x$use_ve" = "xY" -o "x$use_ve" = "x" -o "x$use_ve" = "xy" ]; then
        # Install the virtualenv and run the test suite in it
        python pkg/install_venv.py $installvenvopts
        wrapper=${with_venv}
      fi
    fi
  fi
fi

# Delete old coverage data from previous runs
if [ $coverage -eq 1 ]; then
    ${wrapper} coverage erase
fi

if [ $just_pep8 -eq 1 ]; then
    run_pep8
    exit
fi

run_tests

if [ -z "$noseargs" ]; then
  if [ $no_pep8 -eq 0 ]; then
    run_pep8
  fi
fi

function run_coverage {
    cov_opts="--omit=`pwd`/src/leap/base/tests/*,`pwd`/src/leap/eip/tests/*,`pwd`/src/leap/gui/tests/*"
    cov_opts="$cov_opts,`pwd`/src/leap/util/tests/* "
    cov_opts="$cov_opts --include=`pwd`/src/leap/*" #,`pwd`/src/leap/eip/*"
    ${wrapper} coverage html -d docs/covhtml -i $cov_opts
    echo "now point your browser at docs/covhtml/index.html"
}

if [ $coverage -eq 1 ]; then
    echo "Generating coverage report in docs/covhtml/"
    run_coverage
    exit
fi

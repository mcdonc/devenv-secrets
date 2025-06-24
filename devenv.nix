{ ... }:

{
  imports = [ ./default.nix ];

  secrets.enable = true;
  secrets.profile = "testenv";

  enterShell = ''
    [ "$(secrets)" == "testenv" ] && echo "enterShell works" || exit 2
    env | grep MYSECRET || exit 2
    secrets export | grep MYSECRET || exit 2
  '';

  enterTest = ''
    secretspyexe -m coverage run "$DEVENV_ROOT/test.py"
    secretspyexe -m coverage report -m \
      --fail-under=100 \
      --include="test.py,secrets.py"
  '';
}
